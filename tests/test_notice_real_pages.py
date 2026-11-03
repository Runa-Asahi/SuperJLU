"""用真实页面（2026-11 抓取）核对正文/附件解析。"""
import urllib.parse
from pathlib import Path

from jlu_toolkit import college, oa

FIX = Path(__file__).parent / "fixtures"


def _read(p):
    return (FIX / p).read_bytes().decode("utf-8", "replace")


def test_oa_real_detail_body_and_attachments():
    d = oa.parse_detail(_read("oa/detail_71736581.html"))
    assert d["title"].startswith("关于开展2026年度")
    assert d["text"].startswith("各学院：") and "党委学生工作部" in d["text"]
    assert "style=" not in d["html"] and "<span" not in d["html"]
    names = [a["name"] for a in d["attachments"]]
    assert len(names) == 6 and names[0] == "附件1：吉林大学“2+3”辅导员专项考核工作实施办法.pdf"
    u = d["attachments"][1]["url"]
    assert u.startswith("https://oa.jlu.edu.cn/defaultroot/rd/download/attachdownload.jsp?res=")
    # 与 OA 服务端 BASEEncoderAjax.jsp 对同一附件的输出一致（在校园网内实际下载核对过）
    assert urllib.parse.unquote(u.split("res=")[1]).startswith(
        "VFdwQmVVNXFSWGhOUkUxM1QxUkZkMDFVWXpOTmFrVXpUV3BOTUU5VVZUQk5lVFUwWWtoT05GRlBiVnBvVDFNM2RHcE1kblpL")


def test_oa_encoder_matches_server():
    res = oa.attach_url("2026110309101223920408755.pdf", "附件1：吉林大学“2+3”辅导员专项考核工作实施办法.pdf",
                        "71736581")
    server = ("VFdwQmVVNXFSWGhOUkUxM1QxUkZkMDFVU1hsTmVtdDVUVVJSZDA5RVl6Rk9VelYzV2tkYVFUWmFi"
              "VVUxVEhVeVRXVXJPRzExVjFGcApaV0ZsYkN0WGEzQXJWM1J3ZFV0QmJrUkpjZ3BOSzB0QmJtVnBL"
              "MmhsVjNaMlQxZFNiVTlUTkdzcmJXaDFaV2xCWnl0aFozVlBWek53ClpWTTViazlYZFc1MVlWZDJa"
              "VmRMYm5WaGVteFROWGRhUjFwQlRucEZNMDE2V1RGUFJFVTlkMmhwY2c9PQ==")
    assert urllib.parse.unquote(res.split("res=")[1]) == server


def test_oa_real_detail_images_and_table():
    d = oa.parse_detail(_read("oa/detail_71711774.html"))
    assert d["html"].count("<img") == 6 and "<table>" in d["html"]
    assert 'src="https://oa.jlu.edu.cn/defaultroot/upload/html/' in d["html"]
    assert d["attachments"] == []


def _col(name, ch, url):
    return college.fetch_detail({"channel": ch, "url": url}, getter=lambda u: _read(f"college/{name}"))


def test_hospital_bodies():
    d = _col("jdyy_detail.html", "jdyy-kx", "https://www.jdyy.cn/index.php?m=home&c=View&a=index&aid=87413")
    assert d["text"].startswith("10月25日") and "发布时间" not in d["text"] and d["html"].count("<img") == 5
    d = _col("jdey_detail.html", "jdey-xwdt", "https://www.jdey.com.cn/xwzx3/xwdt2/content_105728.html")
    assert d["text"].startswith("为深入贯彻落实") and d["html"].count("<img") == 10
    d = _col("zrlyyy_detail.html", "zrlyyy-xxgg", "https://www.zrlyyy.com/wujia_detail_g7yU_59/233772.html")
    assert d["text"].startswith("根据我院非编岗位") and "请输入关键字" not in d["text"]
    assert [a["name"] for a in d["attachments"]] == ["录取结果26-6-1、26-8.xls"]


def test_body_images_go_through_local_proxy():
    from jlu_toolkit import ui
    it = ui._oa_item({"id": "1", "url": "https://oa.jlu.edu.cn/defaultroot/x",
                      "html": '<p><img src="https://oa.jlu.edu.cn/defaultroot/upload/html/a.jpg?x=1&amp;y=2"></p>'},
                     full=True)
    assert 'src="/api/oa/img?u=https%3A%2F%2Foa.jlu.edu.cn%2Fdefaultroot%2Fupload%2Fhtml%2Fa.jpg%3Fx%3D1%26y%3D2"' in it["html"]


def test_image_proxy_rejects_other_hosts_and_non_images(monkeypatch):
    import pytest
    from jlu_toolkit import ui
    for bad in ("https://evil.example/a.png", "file:///etc/passwd", "https://u@csw.jlu.edu.cn/a.png"):
        with pytest.raises(ValueError):
            ui.notice_img(bad)
    monkeypatch.setattr(college, "get_bytes", lambda u, t=10, limit=0: b"<html>login</html>")
    with pytest.raises(ValueError):
        ui.notice_img("https://csw.jlu.edu.cn/a.png")
    monkeypatch.setattr(college, "get_bytes", lambda u, t=10, limit=0: b"\x89PNG\r\n\x1a\nxx")
    assert ui.notice_img("https://www.jdey.com.cn/b.png")[1] == "image/png"
