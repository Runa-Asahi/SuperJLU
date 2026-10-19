import json
import re
import shutil
import subprocess
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from jlu_toolkit import ui, ui_prefs
from jlu_toolkit.ui_page import PAGE


@pytest.fixture
def server(tmp_path):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(ui.Store(tmp_path)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", tmp_path
    srv.shutdown(); srv.server_close()


def _post(base, body):
    req = urllib.request.Request(base + "/api/prefs", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def test_roundtrip_survives_new_server(server, tmp_path):
    base, root = server
    assert _post(base, {"set": {"jlu-theme": "dark", "jlu-grade-pinned": "[1]"}})["prefs"]["jlu-theme"] == "dark"
    assert json.load(urllib.request.urlopen(base + "/api/prefs"))["prefs"]["jlu-grade-pinned"] == "[1]"
    # 换端口（新进程）后仍能读到，并注入到页面首帧脚本之前
    srv = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(ui.Store(root)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        html = urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}/").read().decode()
    finally:
        srv.shutdown(); srv.server_close()
    i = html.index('window.__PREFS={"jlu-theme": "dark"')
    assert i < html.index("首帧前应用主题")
    assert _post(base, {"remove": ["jlu-theme"]})["prefs"] == {"jlu-grade-pinned": "[1]"}


def test_post_needs_json_content_type(server):
    base, _ = server
    req = urllib.request.Request(base + "/api/prefs", data=b"{}", headers={"Content-Type": "text/plain"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 403


def test_whitelist_and_limits(tmp_path):
    p = ui_prefs.update(tmp_path, {"jlu-ok": "1", "token": "x", "jlu-big": "x" * 5000,
                                   "jlu-num": 3, "jlu-<bad>": "1"})
    assert p == {"jlu-ok": "1"}
    p = ui_prefs.update(tmp_path, {f"jlu-k{i}": "v" for i in range(100)})
    assert len(p) <= ui_prefs.MAX_KEYS
    assert len(json.dumps(ui_prefs.load(tmp_path))) <= ui_prefs.MAX_TOTAL
    (tmp_path / ui_prefs.FILE).write_text("not json", encoding="utf-8")
    assert ui_prefs.load(tmp_path) == {}


def test_injection_escaping(tmp_path):
    ui_prefs.update(tmp_path, {"jlu-x": "</script><script>alert(1)</script>&"})
    s = ui_prefs.inline_script(tmp_path)
    inner = s[len("<script>"):-len("</script>")]
    assert "<" not in inner and ">" not in inner and "&" not in inner
    assert json.loads(inner[len("window.__PREFS="):-1])["jlu-x"].startswith("</script>")


def test_theme_script_reads_prefs_first():
    m = re.search(r"<script>(/\* 首帧前应用主题.*?)</script>", PAGE)
    js = m.group(1)
    assert js.index("window.__PREFS") < js.index('localStorage.getItem("jlu-theme")')
    assert "/api/prefs" in js and "keepalive" in js


@pytest.mark.skipif(not shutil.which("node"), reason="node missing")
def test_theme_script_behaviour_in_node(tmp_path):
    js = re.search(r"<script>(/\* 首帧前应用主题.*?)</script>", PAGE).group(1)
    harness = """
var store={"jlu-theme":"light"},posts=[],attrs={};
function Storage(){}Storage.prototype.getItem=function(k){return k in store?store[k]:null};
Storage.prototype.setItem=function(k,v){store[k]=String(v)};Storage.prototype.removeItem=function(k){delete store[k]};
var window={__PREFS:{"jlu-theme":"dark"}};window.localStorage=new Storage();var localStorage=window.localStorage;
var document={documentElement:{setAttribute:function(a,v){attrs[a]=v},removeAttribute:function(a){delete attrs[a]}},
getElementById:function(){return null},querySelectorAll:function(){return []}};
function fetch(u,o){posts.push(JSON.parse(o.body));return {catch:function(){}}}
""" + js + """
if(attrs["data-theme"]!=="dark"||store["jlu-theme"]!=="dark")throw new Error("prefs not applied "+JSON.stringify([attrs,store]));
window.__setTheme("system");
if("jlu-theme" in store||JSON.stringify(posts[posts.length-1])!=='{"remove":["jlu-theme"]}')throw new Error("no sync");
localStorage.setItem("other","1");if(posts.length!==1)throw new Error("non jlu synced");
"""
    f = tmp_path / "h.js"; f.write_text(harness, encoding="utf-8")
    subprocess.run(["node", str(f)], check=True)
