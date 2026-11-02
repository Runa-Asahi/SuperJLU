"""Synthetic school responses only: tests must never submit real recalculations."""
import json
from types import SimpleNamespace

import pytest

from jlu_toolkit import academic, jwxt, secure_store, ui


@pytest.fixture
def setup(monkeypatch, tmp_path):
    row = {"XH": "synthetic-user", "PYFADM": "synthetic-plan", "CZSJ": "T1"}
    calls = {"summary": 0, "completion": 0, "curriculum": 0}
    def summary(client):
        calls["summary"] += 1
        return dict(row)
    def completion(*args, **kwargs):
        calls["completion"] += 1
        return {"required": 160, "earned": 0, "groups": [], "calculated_at": row["CZSJ"]}
    def curriculum(*args, **kwargs):
        calls["curriculum"] += 1
        return {"courses": [{"name": "Synthetic", "code": "A", "status": "未修", "credit": 2}],
                "count": 1, "source": {}}
    monkeypatch.setattr(academic, "summary", summary)
    monkeypatch.setattr(academic.meta, "fetch_completion", completion)
    monkeypatch.setattr(academic.plan, "fetch_plan", curriculum)
    return tmp_path, row, calls


def complete(root, force=False):
    task = academic.Sync(object(), root, force=force)
    return task.completion(), task.curriculum()


def test_cached_sync_only_checks_time_and_preserves_content(setup, monkeypatch):
    root, row, calls = setup
    monkeypatch.setattr(academic, "now", lambda: "local-T1")
    complete(root)
    before = secure_store.load_json(root / "completion.json")
    row["CZSJ"] = "T2"
    monkeypatch.setattr(academic, "now", lambda: "local-T2")
    result = complete(root)
    assert all(r["cached"] for r in result)
    assert calls == {"summary": 2, "completion": 1, "curriculum": 1}
    assert secure_store.load_json(root / "completion.json") == before
    info = academic.state(root)
    assert info["local_synced_at"] == "local-T1"
    assert info["checked_at"] == "local-T2"
    assert info["school_calculated_at"] == "T2" and info["cached_calculated_at"] == "T1"
    assert "synthetic-user" not in (root / "academic_meta.json").read_text()
    assert "owner" not in ui.Store(root).snapshot()["academic_meta"]


def test_force_and_changed_owner_cannot_reuse_previous_cache(setup):
    root, row, calls = setup
    complete(root)
    complete(root, force=True)
    row["XH"] = "other-synthetic-user"
    complete(root)
    assert calls["completion"] == calls["curriculum"] == 3


def test_missing_or_failed_curriculum_is_not_treated_as_complete_cache(setup, monkeypatch):
    root, row, calls = setup
    task = academic.Sync(object(), root)
    task.completion()
    assert academic.state(root)["curriculum_ready"] is False
    complete(root)
    assert calls["completion"] == 2 and calls["curriculum"] == 1


def test_failed_light_check_keeps_times_and_does_not_fetch_curriculum(setup, monkeypatch):
    root, row, calls = setup
    complete(root)
    before = academic.state(root)
    def fail(client):
        raise jwxt.NetworkError("synthetic network failure")
    monkeypatch.setattr(academic, "summary", fail)
    task = academic.Sync(object(), root)
    with pytest.raises(jwxt.NetworkError):
        task.completion()
    assert task.curriculum()["ok"] is False
    assert calls["curriculum"] == 1
    assert academic.state(root) == before


def test_recalculation_requires_confirmation_and_deduplicates_busy_jobs(tmp_path):
    job = academic.Recalculator(ui.Store(tmp_path), lambda: None)
    with pytest.raises(ValueError):
        job.start()
    job.job = {"state": "running", "message": "synthetic"}
    assert job.start(True)["state"] == "running"


def test_recalculation_ignores_old_progress_then_syncs_only_after_new_timestamp(setup, monkeypatch):
    root, row, calls = setup
    complete(root)
    requests = []
    def post(client, path, fields, app):
        requests.append((path, fields))
        if path.endswith("bysc.do"):
            return {"code": "0"}
        assert path.endswith("byscjd.do")
        if sum(p.endswith("byscjd.do") for p, _ in requests) > 1:
            row["CZSJ"] = "T2"
        return {"datas": {"byscjd": {"rows": [{"YWCS": "1", "ZS": "1"}]}}}
    monkeypatch.setattr(academic.meta, "_post", post)
    monkeypatch.setattr(academic, "time", SimpleNamespace(monotonic=lambda: 0, sleep=lambda _: None))
    job = academic.Recalculator(ui.Store(root), lambda: object())
    job.run(timeout=5, interval=0)
    assert job.status()["state"] == "success"
    assert sum(p.endswith("bysc.do") for p, _ in requests) == 1
    assert sum(p.endswith("byscjd.do") for p, _ in requests) == 2
    assert requests[0][1] == {"XH": row["XH"], "PYFADM": row["PYFADM"], "BYNJDM": "-", "SCLBDM": "04"}
    assert calls["completion"] == calls["curriculum"] == 2
    assert academic.state(root)["cached_calculated_at"] == "T2"


def test_recalculation_timeout_never_retries_submission_or_changes_cache(setup, monkeypatch):
    root, row, calls = setup
    complete(root)
    before = secure_store.load_json(root / "completion.json")
    requests = []
    def post(client, path, fields, app):
        requests.append(path)
        return {"code": "0"}
    monkeypatch.setattr(academic.meta, "_post", post)
    monkeypatch.setattr(academic, "time", SimpleNamespace(monotonic=lambda: 0, sleep=lambda _: None))
    job = academic.Recalculator(ui.Store(root), lambda: object())
    job.run(timeout=0)
    assert job.status()["state"] == "unconfirmed"
    assert len(requests) == 1 and requests[0].endswith("bysc.do")
    assert secure_store.load_json(root / "completion.json") == before


def test_failed_submit_is_not_automatically_replayed(setup, monkeypatch):
    root, row, calls = setup
    attempts = []
    def fail(*args):
        attempts.append(True)
        raise jwxt.NetworkError("synthetic failure after send")
    monkeypatch.setattr(academic.meta, "_post", fail)
    job = academic.Recalculator(ui.Store(root), lambda: object())
    job.run()
    assert len(attempts) == 1 and job.status()["state"] == "unconfirmed"
