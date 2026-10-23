"""Daily availability: complete results only, isolated sessions and cache bounds."""
import json
from http.cookiejar import CookieJar

import pytest

from jlu_toolkit import jwxt, rooms, ui


@pytest.fixture
def daily(tmp_path, monkeypatch):
    store = ui.Store(tmp_path)
    store.p("rooms_profile.json").write_text('{"endpoint":"test","scheme":"test"}', encoding="utf-8")

    class Client:
        route = "direct"
        jar = CookieJar()
        saves = 0
        warmups = 0

        def enter_emap_app(self, app):
            self.warmups += 1

        def save_session(self):
            self.saves += 1

    client = Client()
    monkeypatch.setattr(ui, "_client", lambda: client)
    def clone(c):
        child = Client()
        child.route = c.route
        child.jar = jwxt.jar_from_list(jwxt.jar_to_list(c.jar))
        return child
    monkeypatch.setattr(ui, "_room_query_client", clone)
    calls = []

    def query(c, q, profile, **kwargs):
        calls.append((q, kwargs))
        return [rooms.Room("R101", "楼 A", "示例校区")], {}

    monkeypatch.setattr(rooms, "query_rooms", query)
    monkeypatch.setattr(rooms, "cached_meta", lambda c: {"fields": []})
    body = {"campus": "01", "building": "B1", "date": "2026-10-22", "periods": "12"}
    return store, client, calls, body


def test_period12_complete_cache_scope_and_logout(daily, monkeypatch):
    store, client, calls, body = daily
    a = ui.room_day_period_api(store, body)
    assert a["period"] == 12 and a["date"] == body["date"] and a["complete"]
    assert a["rooms"] == [{**rooms.Room("R101", "楼 A", "示例校区").to_dict(), "special": False}]
    assert not a["cached"] and client.saves == 1
    assert calls[0][1]["require_complete"] and calls[0][1]["enter_app"] is False
    assert ui.room_day_period_api(store, body)["cached"]
    assert len(calls) == 1
    for field, value in [("date", "2026-10-23"), ("building", "B2"), ("campus", "02"), ("kind", "K2"), ("seat_min", 30)]:
        ui.room_day_period_api(store, {**body, field: value})
    client.route = "webvpn"
    assert not ui.room_day_period_api(store, body)["cached"]
    client.jar = jwxt.jar_from_list([{"name": "ticket", "value": "synthetic", "domain": "cas.jlu.edu.cn", "path": "/"}])
    assert not ui.room_day_period_api(store, body)["cached"]
    monkeypatch.setattr(ui, "_client", lambda: (_ for _ in ()).throw(jwxt.LoginError("已退出")))
    with pytest.raises(jwxt.LoginError):
        ui.room_day_period_api(store, body)


def test_cache_expires_and_is_bounded(daily, monkeypatch):
    import time
    store, client, calls, body = daily
    now = [1000]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])
    ui.room_day_period_api(store, body)
    now[0] += 301
    assert not ui.room_day_period_api(store, body)["cached"]
    assert len(calls) == 2
    for n in range(40):
        now[0] += 1
        ui.room_day_period_api(store, {**body, "building": str(n)})
    assert len(store.room_day_cache) == 36


@pytest.mark.parametrize("patch", [{"periods": "9-12"}, {"periods": "13"}, {"mode": "week", "weeks": "6-7", "weekday": 4}])
def test_reject_ranges_or_multiple_dates(daily, patch):
    store, client, calls, body = daily
    with pytest.raises(ValueError, match="单个日期"):
        ui.room_day_period_api(store, {**body, **patch})
    assert not calls


def test_failed_period_not_cached_and_lock_released(daily, monkeypatch):
    store, client, calls, body = daily
    monkeypatch.setattr(rooms, "query_rooms", lambda *a, **kw: (_ for _ in ()).throw(jwxt.NetworkError("断开", "network")))
    with pytest.raises(jwxt.NetworkError):
        ui.room_day_period_api(store, body)
    assert not store.room_day_cache and not store.room_day_lock.locked() and client.saves == 1


def test_daily_requires_prior_success_and_serializes(daily):
    store, client, calls, body = daily
    store.room_day_lock.acquire()
    try:
        with pytest.raises(ValueError, match="正在加载"):
            ui.room_day_period_api(store, body)
    finally:
        store.room_day_lock.release()
    store.p("rooms_profile.json").unlink()
    with pytest.raises(ValueError, match="请先查询"):
        ui.room_day_period_api(store, body)


@pytest.mark.parametrize("response", [(502, ""), (200, "bad json"), (200, '{"datas":{"x":{"rows":[]}}}')])
def test_partial_pagination_never_establishes_absence(response):
    class Client:
        def post_raw(self, *args):
            return *response, ""

    first = {"datas": {"x": {"rows": [{"JASMC": "101"}], "totalSize": 3}}}
    with pytest.raises(jwxt.JwxtError, match="未获取完整"):
        rooms.fetch_all_pages(Client(), "test", {"pageSize": 1}, first, first["datas"]["x"]["rows"], True)


def test_complete_paging_can_mark_absence():
    class Client:
        def post_raw(self, *args):
            return 200, json.dumps({"datas": {"x": {"rows": [{"JASMC": "102"}]}}}), ""

    first = {"datas": {"x": {"totalSize": 2}}}
    assert len(rooms.fetch_all_pages(Client(), "test", {"pageSize": 1}, first, [{"JASMC": "101"}], True)) == 2
    # Without totalSize, an empty final page is a valid end of pagination.
    class Empty:
        def post_raw(self, *args):
            return 200, '{"datas":{"x":{"rows":[]}}}', ""

    assert rooms.fetch_all_pages(Empty(), "test", {"pageSize": 1}, {}, [{"JASMC": "101"}], True)


def test_no_paging_metadata_cannot_confirm_complete():
    with pytest.raises(jwxt.JwxtError, match="分页信息"):
        rooms.fetch_all_pages(None, "test", {}, {}, [], True)


def test_batch_reuses_app_entry_and_saves_once(daily):
    store, client, calls, body = daily
    result = ui.room_day_api(store, {**body, "day_periods": [1, 2, 3, 4]})
    assert [r["period"] for r in result["records"]] == [1, 2, 3, 4]
    assert not result["partial"] and len(calls) == 4 and client.saves == 1
    assert client.warmups == 1
    assert all(options["enter_app"] is False for q, options in calls)
    assert all(options["meta"] == {"fields": []} for q, options in calls)
    repeated = ui.room_day_api(store, {**body, "day_periods": [1, 2, 3, 4]})
    assert all(r["cached"] for r in repeated["records"])
    assert len(calls) == 4 and client.saves == 1


def test_batch_partial_success_can_be_retried(daily, monkeypatch):
    store, client, calls, body = daily
    query = rooms.query_rooms
    def broken(c, q, profile, **kw):
        if q.start == 3:
            raise jwxt.NetworkError("synthetic outage", "network")
        return query(c, q, profile, **kw)
    monkeypatch.setattr(rooms, "query_rooms", broken)
    result = ui.room_day_api(store, {**body, "day_periods": [1, 2, 3, 4]})
    assert result["partial"] and result["failed_period"] == 3
    assert [r["period"] for r in result["records"]] == [1, 2, 4]
    assert len(store.room_day_cache) == 3 and not store.room_day_lock.locked()
    monkeypatch.setattr(rooms, "query_rooms", query)
    result = ui.room_day_api(store, {**body, "day_periods": [1, 2, 3, 4]})
    assert not result["partial"]
    assert [r["cached"] for r in result["records"]] == [True, True, False, True]


@pytest.mark.parametrize("periods", [[], [1, 2, 3, 4, 5], [True], [0], [13], [1, 1], ["1"], None])
def test_batch_limits_school_requests(daily, periods):
    store, client, calls, body = daily
    with pytest.raises(ValueError):
        ui.room_day_api(store, {**body, "day_periods": periods})
    assert not calls


def test_pair_query_is_one_range_and_separate_from_single_cache(daily, monkeypatch):
    store, client, calls, body = daily
    requests = []
    def query(c, q, profile, **kwargs):
        requests.append((q.start, q.end))
        # R101 is free only in period 9; R102 is free in both.
        found = [rooms.Room("R102", "楼 A")]
        if q.start == q.end == 9:
            found.append(rooms.Room("R101", "楼 A"))
        return found, {}
    monkeypatch.setattr(rooms, "query_rooms", query)
    pair = ui.room_day_api(store, {**body, "day_ranges": [[9, 10]]})
    assert requests == [(9, 10)]
    record = pair["records"][0]
    assert record["range"] == [9, 10] and "period" not in record
    assert [r["name"] for r in record["rooms"]] == ["R102"]
    assert ui.room_day_api(store, {**body, "day_ranges": [[9, 10]]})["records"][0]["cached"]
    singles = ui.room_day_api(store, {**body, "day_periods": [9, 10]})
    assert requests == [(9, 10), (9, 9), (10, 10)]
    assert len(singles["records"][0]["rooms"]) == 2
    assert len(singles["records"][1]["rooms"]) == 1


def test_pair_batch_partial_retry_and_app_entry(daily, monkeypatch):
    store, client, calls, body = daily
    def query(c, q, profile, **kwargs):
        if q.start == 3:
            raise jwxt.NetworkError("synthetic", "network")
        calls.append(((q.start, q.end), kwargs))
        return [], {}
    monkeypatch.setattr(rooms, "query_rooms", query)
    result = ui.room_day_api(store, {**body, "day_ranges": [[1, 2], [3, 4]]})
    assert result["partial"] and result["records"][0]["range"] == [1, 2]
    assert len(store.room_day_cache) == 1 and not store.room_day_lock.locked()
    assert result["records"][0]["rooms"] == []
    client.route = "webvpn"
    assert not ui.room_day_api(store, {**body, "day_ranges": [[1, 2]]})["records"][0]["cached"]


@pytest.mark.parametrize("ranges", [None, [], [[1, 2]] * 2, [[2, 3]], [[1, 3]], [[11, 13]], [[True, 2]], [[1]], [1], [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]])
def test_invalid_pair_batches_rejected(daily, ranges):
    store, client, calls, body = daily
    with pytest.raises(ValueError):
        ui.room_day_api(store, {**body, "day_ranges": ranges})
    assert not calls


def test_cannot_mix_pair_and_single_requests(daily):
    store, client, calls, body = daily
    with pytest.raises(ValueError):
        ui.room_day_api(store, {**body, "day_ranges": [[1, 2]], "day_periods": [1]})
    assert not calls


def test_four_queries_really_overlap_with_isolated_clients(daily, monkeypatch):
    import threading
    store, client, calls, body = daily
    barrier = threading.Barrier(4)
    seen = []
    def query(c, q, profile, **kwargs):
        seen.append((c, q.start, kwargs))
        assert c is not client and c.jar is not client.jar
        c.jar.set_cookie(next(iter(jwxt.jar_from_list([
            {"name": "worker", "value": str(q.start), "domain": "iedu.jlu.edu.cn", "path": "/"}]))))
        barrier.wait(timeout=5)  # A serial implementation cannot pass.
        assert next(iter(c.jar)).value == str(q.start)
        return [rooms.Room(str(q.start), "test")], {}
    monkeypatch.setattr(rooms, "query_rooms", query)
    result = ui.room_day_api(store, {**body, "day_periods": [1, 2, 3, 4]})
    assert not result["partial"] and len({id(c) for c, _, _ in seen}) == 4
    assert len(client.jar) == 0 and client.saves == client.warmups == 1
    assert [r["rooms"][0]["name"] for r in result["records"]] == ["1", "2", "3", "4"]
    assert all(kw["profile_data"] == {"endpoint": "test", "scheme": "test"} for _, _, kw in seen)


def test_warmup_reused_across_batches_and_scoped_to_session(daily, monkeypatch):
    import time
    store, client, calls, body = daily
    now = [100.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])
    ui.room_day_api(store, {**body, "day_periods": [1, 2, 3, 4]})
    ui.room_day_api(store, {**body, "day_periods": [5, 6, 7, 8]})
    assert client.warmups == 1 and client.saves == 1
    now[0] += 61
    ui.room_day_api(store, {**body, "day_periods": [9]})
    assert client.warmups == 2
    client.route = "webvpn"
    ui.room_day_api(store, {**body, "day_periods": [10]})
    assert client.warmups == 3
    client.jar = jwxt.jar_from_list([{"name": "session", "value": "new", "domain": "iedu.jlu.edu.cn", "path": "/"}])
    ui.room_day_api(store, {**body, "day_periods": [11]})
    assert client.warmups == 4


def test_one_expired_worker_never_gets_overwritten_by_success(daily, monkeypatch):
    store, client, calls, body = daily
    def query(c, q, profile, **kwargs):
        if q.start == 2:
            # Coordinator must have saved before queries, never after expiry.
            assert client.saves == 1
            raise jwxt.SessionExpiredError()
        return [rooms.Room("R101")], {}
    monkeypatch.setattr(rooms, "query_rooms", query)
    result = ui.room_day_api(store, {**body, "day_periods": [1, 2, 3, 4]})
    assert result["partial"] and result["session_expired"]
    assert [r["period"] for r in result["records"]] == [1, 3, 4]
    assert result["failed_periods"] == [2] and store.room_day_warm is None
    assert client.saves == 1


def test_real_worker_clone_does_not_share_mutable_network_state():
    parent = jwxt.JwxtClient(route="webvpn")
    parent.jar = jwxt.jar_from_list([{"name": "auth", "value": "synthetic", "domain": "iedu.jlu.edu.cn", "path": "/"}])
    parent._native_hosts.add("iedu.jlu.edu.cn")
    child = ui._room_query_client(parent)
    assert child.jar is not parent.jar and child.opener is not parent.opener
    assert child._native_hosts == parent._native_hosts and child._native_hosts is not parent._native_hosts
    assert child.route == parent.route and child.timeout == parent.timeout
    assert child._vpn_cookies_loaded and not child._restore_saved_cas
    assert not child.try_cas_refresh()
    next(iter(child.jar)).value = "worker-only"
    assert next(iter(parent.jar)).value == "synthetic"


def test_parallel_profile_snapshot_never_written(tmp_path):
    profile = tmp_path / "profile.json"
    profile.write_text("unchanged", encoding="utf-8")
    class Client:
        def post_raw(self, *args):
            return 200, json.dumps({"datas": {"cxkxjs": {"totalSize": 1, "rows": [{"JASMC": "101"}]}}}), "https://iedu.jlu.edu.cn/query"
    found, _ = rooms.query_rooms(Client(), rooms.RoomQuery("01", "2026-10-22", 1, 1), profile,
        meta={"fields": []}, max_tries=1, require_complete=True, enter_app=False,
        profile_data={"endpoint": rooms.ENDPOINTS[0], "scheme": "form_kxrq_ksjc"})
    assert found[0].name == "101" and profile.read_text(encoding="utf-8") == "unchanged"


def test_complete_query_detects_login_redirect():
    class Client:
        def post_raw(self, *args):
            return 200, "<html>loginForm</html>", "https://cas.jlu.edu.cn/tpass/login"
    with pytest.raises(jwxt.SessionExpiredError):
        rooms.query_rooms(Client(), rooms.RoomQuery("01", "2026-10-22", 1, 1),
                          meta={"fields": []}, max_tries=1, require_complete=True, enter_app=False)
