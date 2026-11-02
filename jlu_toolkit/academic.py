"""Academic cache policy and explicit school-side recalculation.

Query endpoints remain read-only. bysc.do is called only by a confirmed job;
it is never registered with endpoint discovery or ordinary sync.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import threading
import time
import uuid

from . import endpoints, jwxt, meta, plan, secure_store


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def summary(client):
    client.enter_emap_app(meta.APP_XYWCCX)
    rows = meta._rows(meta._post(client, meta.EP_COMPLETION,
                     {"SCLBDM": "04", "*order": "-CZSJ"}, meta.APP_XYWCCX), "cxxsscfa")
    return rows[0] if rows else {}


def owner(row):
    fields = [str(row.get(k) or "") for k in ("XH", "PYFADM")]
    return hashlib.sha256(json.dumps(fields).encode()).hexdigest() if all(fields) else None


def state(root):
    try:
        result = json.loads((Path(root) / "academic_meta.json").read_text(encoding="utf-8"))
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(root, value):
    path = Path(root) / "academic_meta.json"
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


class Sync:
    def __init__(self, client, root, *, force=False, grades=None, courses_now=None):
        self.client, self.root, self.force = client, Path(root), force
        self.grades, self.courses_now = grades, courses_now
        self.cached = False
        self.completion_written = False
        self.row = None

    def completion(self):
        self.row = summary(self.client)
        info = state(self.root)
        cached = secure_store.load_json(self.root / "completion.json")
        curriculum = secure_store.load_json(self.root / "plan_courses.json")
        valid = (info.get("curriculum_ready") is True and isinstance(cached, dict) and bool(cached) and
                 isinstance(curriculum, dict) and bool(curriculum.get("courses") or curriculum.get("tree_nodes")))
        same_owner = owner(self.row) is not None and info.get("owner") == owner(self.row)
        if not self.force and valid and same_owner:
            self.cached = True
            info.update(checked_at=now(), school_calculated_at=str(self.row.get("CZSJ") or ""))
            write_state(self.root, info)
            return {"ok": True, "cached": True}
        comp = meta.fetch_completion(self.client, grades=self.grades)
        if same_owner and curriculum:
            comp = plan.attach_to_completion(comp, curriculum)
        secure_store.save_json(self.root / "completion.json", endpoints.scrub(comp))
        self.completion_written = True
        # A changed owner must not inherit the preceding account's curriculum.
        # Cache reuse requires both modules to have succeeded for this owner.
        info = {"owner": owner(self.row), "checked_at": now(), "local_synced_at": info.get("local_synced_at") if same_owner else None,
                "school_calculated_at": str(self.row.get("CZSJ") or ""),
                "cached_calculated_at": info.get("cached_calculated_at", "") if same_owner else "",
                "overview_calculated_at": str(comp.get("calculated_at") or ""),
                "curriculum_ready": False}
        write_state(self.root, info)
        return {"ok": True, "cached": False, "groups": len(comp.get("groups") or [])}

    def curriculum(self):
        if not self.cached and not self.completion_written:
            return {"ok": False, "error": "学业查询未完成，培养方案缓存未更新"}
        if self.cached:
            return {"ok": True, "cached": True}
        data = plan.fetch_plan(self.client, grades=self.grades, courses_now=self.courses_now)
        if not data.get("courses") and not data.get("tree_nodes"):
            raise jwxt.JwxtError("教务未返回培养方案课程明细，已保留原缓存")
        secure_store.save_json(self.root / "plan_courses.json", endpoints.scrub(data))
        comp = secure_store.load_json(self.root / "completion.json")
        if comp:
            secure_store.save_json(self.root / "completion.json", endpoints.scrub(plan.attach_to_completion(comp, data)))
        info = state(self.root)
        info.update(curriculum_ready=True, local_synced_at=now(),
                    cached_calculated_at=str((comp or {}).get("calculated_at") or info.get("school_calculated_at") or ""))
        write_state(self.root, info)
        return {"ok": True, "cached": False, "count": data.get("count", len(data.get("courses") or []))}


class Recalculator:
    """One job per local server; a timeout never re-submits a school write."""
    def __init__(self, store, client_factory):
        self.store, self.client_factory = store, client_factory
        self.lock = threading.Lock()
        self.job = {"state": "idle"}

    def status(self):
        with self.lock:
            return dict(self.job)

    def update(self, **values):
        with self.lock:
            self.job.update(values)

    def start(self, confirmed=False):
        if confirmed is not True:
            raise ValueError("请先确认请求教务重新计算学业完成情况")
        with self.lock:
            if self.job["state"] in ("submitting", "running", "syncing"):
                return dict(self.job)
            self.job = {"state": "submitting", "message": "正在请求教务重新计算…"}
        threading.Thread(target=self.run, daemon=True, name="academic-recalculation").start()
        return self.status()

    def run(self, *, timeout=120, interval=2):
        submitted = False
        try:
            client = self.client_factory()
            before = summary(client)
            target = before
            if not target.get("PYFADM") or not target.get("XH"):
                rows = meta._rows(meta._post(client, "/jwapp/sys/xywccx/modules/xywccx/grpyfacx.do",
                                           {}, meta.APP_XYWCCX), "grpyfacx")
                majors = [r for r in rows if str(r.get("XDLXDM")) == "01"]
                candidates = majors or rows
                if len(candidates) != 1:
                    raise jwxt.JwxtError("无法唯一确定培养方案，请先到教务学业完成页面选择方案并计算")
                target = candidates[0]
            if not target.get("PYFADM") or not target.get("XH"):
                raise jwxt.JwxtError("缺少当前账号的培养方案信息，未提交重新计算")
            fields = {k: target[k] for k in ("XH", "PYFADM")}
            fields.update(BYNJDM="-", SCLBDM="04")
            # School xywccx.js actionCount and xywccxBS.js queryZxjd.
            submitted = True
            response = meta._post(client, "/jwapp/sys/xywccx/modules/xywccx/bysc.do", fields, meta.APP_XYWCCX)
            if str(response.get("code")) != "0":
                raise jwxt.JwxtError("教务未确认接受重新计算请求，请到学校页面核对")
            self.update(state="running", message="教务正在重新计算，请稍候…")
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                time.sleep(interval)
                data = meta._post(client, "/jwapp/sys/xywccx/modules/xywccx/byscjd.do",
                                  {"ZXJDKEY": "BYSC_" + str(target["XH"])}, meta.APP_XYWCCX)
                rows = meta._rows(data, "byscjd")
                if not rows:
                    continue
                total, done = meta._f(rows[0].get("ZS")), meta._f(rows[0].get("YWCS"))
                if total is None or done is None or total < 0 or done < 0:
                    continue
                if total > 0:
                    self.update(progress=min(100, int(done / total * 100)))
                if done >= total:
                    latest = summary(client)
                    if (latest.get("PYFADM") != target["PYFADM"] or not latest.get("CZSJ") or
                            latest.get("CZSJ") == before.get("CZSJ")):
                        continue  # Do not mistake last job's 100% for this job's result.
                    self.update(state="syncing", message="计算完成，正在更新课程和学分…")
                    # Another login must not receive this account's job result.
                    if owner(summary(self.client_factory())) != owner(target):
                        raise jwxt.JwxtError("账号已切换，未写入原账号的重算结果")
                    task = Sync(client, self.store.root, force=True, grades=self.store.grades())
                    task.completion()
                    task.curriculum()
                    self.update(state="success", message="已重新计算，课程和学分已更新。", progress=100)
                    return
            self.update(state="unconfirmed", message="教务还没有确认计算完成。请稍后点「从教务更新」，或到教务网站查看；请勿重复计算。")
        except Exception:
            # No raw school response, student number or plan identifier is exposed.
            self.update(state="unconfirmed" if submitted else "failed",
                        message=("尚未确认是否计算完成。请稍后点「从教务更新」，或到教务网站查看。"
                                 if submitted else "暂时无法请求计算，请检查网络与登录，或到教务网站操作。"))
