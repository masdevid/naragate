import random
from datetime import date, timedelta

import pytest

from app.services.policy_signal import (
    aggregate_verdict,
    classify_signal_for_name,
    daily_chunks,
    daily_close_series,
    policy_window_indices,
    returns_in_percent,
)


def synthetic_daily(
    start="2025-09-01",
    days=260,
    base=1000.0,
    vol=0.01,
    policy_dates=None,
    policy_move=0.0,
    seed=0,
) -> list[dict]:
    rng = random.Random(seed)
    price = base
    cur = date.fromisoformat(start)
    dates = set(policy_dates or [])
    out = []
    for _ in range(days):
        r = rng.gauss(0, vol)
        if cur.isoformat() in dates:
            r += rng.choice([-1, 1]) * policy_move
        price = max(10.0, price * (1 + r))
        out.append({"date": cur.isoformat(), "close": round(price, 2), "volume": 1_000_000})
        cur += timedelta(days=1)
    return out


def policy_dates_spread(num=5, start_index=30, span=40) -> list[str]:
    start = date.fromisoformat("2025-09-01")
    return [(start + timedelta(days=start_index + i * span)).isoformat() for i in range(num)]


class TestSeriesHelpers:
    def test_daily_close_series_ascends_drops_bad_rows(self):
        tx = [
            {"date": "2025-09-02", "close": 1200},
            {"date": "2025-09-01", "close": 1000},
            {"date": "2025-09-03", "volume": 5},   # no close -> dropped
            {"date": "2025-09-04", "price": 1400},  # price fallback
        ]
        series = daily_close_series(tx)
        assert series == [("2025-09-01", 1000.0), ("2025-09-02", 1200.0), ("2025-09-04", 1400.0)]

    def test_returns_in_percent(self):
        series = [("d1", 100.0), ("d2", 110.0), ("d3", 99.0)]
        ret = returns_in_percent(series)
        assert [round(r, 2) for _, r in ret] == [10.0, -10.0]

    def test_policy_window_indices_covers_neighbors(self):
        idxs = policy_window_indices(["a", "b", "c", "d", "e", "f"], ["c"], window_days=1)
        assert idxs == {1, 2, 3}


class TestClassification:
    def test_market_priced_names_cluster_on_policy_dates(self):
        dates = policy_dates_spread()
        tx = synthetic_daily(vol=0.01, policy_dates=dates, policy_move=0.08, seed=1)
        result = classify_signal_for_name("ADRO", tx, dates)
        assert result.price_regime == "market_priced"
        assert result.policy_signal == "responsive"
        assert result.classification == "market_priced_signal"
        assert result.policy_ratio >= 2.0

    def test_administered_price_never_clusters(self):
        dates = policy_dates_spread()
        tx = synthetic_daily(vol=0.0004, policy_dates=dates, policy_move=0.0, seed=2)
        result = classify_signal_for_name("PGAS", tx, dates)
        assert result.price_regime == "administered"
        assert result.classification == "administered"
        assert result.policy_ratio < 1.5

    def test_market_priced_but_policy_inert_is_not_a_beacon(self):
        dates = policy_dates_spread()
        tx = synthetic_daily(vol=0.01, policy_dates=dates, policy_move=0.0, seed=3)
        result = classify_signal_for_name("ITMG", tx, dates)
        assert result.price_regime == "market_priced"
        assert result.policy_signal == "inert"
        assert result.classification == "market_priced_no_signal"
        assert not result.is_beacon

    def test_empty_data_reports_failure_not_crash(self):
        result = classify_signal_for_name("ADRO", [], [])
        assert result.error == "no usable close prices"
        assert result.classification == "administered"
        assert result.data_days == 0


class TestVerdict:
    def test_pass_when_two_strong_beacons(self):
        dates = policy_dates_spread()
        tx_a = synthetic_daily(vol=0.01, policy_dates=dates, policy_move=0.08, seed=4)
        tx_b = synthetic_daily(vol=0.012, policy_dates=dates, policy_move=0.08, seed=5)
        a = classify_signal_for_name("ADRO", tx_a, dates)
        b = classify_signal_for_name("ITMG", tx_b, dates)
        verdict, _ = aggregate_verdict([a, b])
        assert verdict == "PASS"
        assert {a.ticker, b.ticker} == {"ADRO", "ITMG"}

    def test_conditional_when_single_beacon(self):
        dates = policy_dates_spread()
        tx = synthetic_daily(vol=0.01, policy_dates=dates, policy_move=0.08, seed=6)
        beacon = classify_signal_for_name("ADRO", tx, dates)
        inert = classify_signal_for_name("PGAS", synthetic_daily(vol=0.0004, seed=7), dates)
        verdict, _ = aggregate_verdict([beacon, inert])
        assert verdict == "CONDITIONAL"

    def test_fail_when_nothing_moves_on_policy(self):
        dates = policy_dates_spread()
        inert = classify_signal_for_name("PGAS", synthetic_daily(vol=0.0004, seed=8), dates)
        verdict, rationale = aggregate_verdict([inert])
        assert verdict == "FAIL"
        assert "falsified" in rationale

    def test_beacon_list_from_report(self):
        dates = policy_dates_spread()
        from app.services.policy_signal import PrecheckReport
        a = classify_signal_for_name("ADRO", synthetic_daily(vol=0.01, policy_dates=dates, policy_move=0.08, seed=9), dates)
        p = classify_signal_for_name("PGAS", synthetic_daily(vol=0.0004, seed=10), dates)
        verdict, rationale = aggregate_verdict([a, p])
        report = PrecheckReport(verdict=verdict, rationale=rationale, window_days=2,
                                policy_events=[{"date": dates[0], "title": "t", "subsector": "s", "description": "d", "verified": False}],
                                results=[a, p])
        assert report.beacon_list == ["ADRO"]


class TestRunPrecheck:
    @pytest.mark.asyncio
    async def test_uses_cache_first(self, monkeypatch):
        dates = policy_dates_spread()
        events: list[PolicyEvent] = [
            {"date": d, "title": f"event {i}", "subsector": "s", "description": "d", "verified": False}
            for i, d in enumerate(dates)
        ]
        tx = synthetic_daily(vol=0.01, policy_dates=dates, policy_move=0.08, seed=11)
        env = {t: {"daily_transaction": tx} for t in ("ADRO", "ITMG", "MEDC", "PGAS", "PTBA")}
        from app.core.evidence_cache import cache
        monkeypatch.setattr(cache, "get", _async_dict_get(env))
        calls = {"n": 0}
        monkeypatch.setattr(
            "app.services.policy_signal.sectors_client.get_daily_transaction",
            _counting_async(calls),
        )
        from app.services.policy_signal import run_precheck
        from app.services.policy_dates import PolicyEvent
        report = await run_precheck(events)
        assert calls["n"] == 0
        assert report.verdict == "PASS"
        assert len(report.beacon_list) >= 2

    @pytest.mark.asyncio
    async def test_fetches_and_merges_on_miss(self, monkeypatch):
        from app.core.evidence_cache import cache
        monkeypatch.setattr(cache, "get", _async_dict_get({}))
        merges = {"n": 0}
        async def fake_merge(ticker, key, value, ttl=None):
            merges["n"] += 1
        monkeypatch.setattr(cache, "merge", fake_merge)
        dates = policy_dates_spread()
        tx = synthetic_daily(vol=0.01, policy_dates=dates, policy_move=0.08, seed=12)
        async def fake_fetch(_ticker, start=None, end=None):
            return tx
        monkeypatch.setattr("app.services.policy_signal.sectors_client.get_daily_transaction", fake_fetch)
        from app.services.policy_signal import run_precheck
        from app.services.policy_dates import PolicyEvent
        report = await run_precheck([{"date": dates[0], "title": "t", "subsector": "s", "description": "d", "verified": False}])
        assert merges["n"] == 5
        assert report.verdict in ("PASS", "CONDITIONAL")


class TestDailyChunks:
    def test_single_chunk_within_max(self):
        start = date(2026, 1, 1)
        chunks = daily_chunks(start, start + timedelta(days=60))
        assert chunks == [("2026-01-01", "2026-03-02")]
        assert (date.fromisoformat(chunks[0][1]) - date.fromisoformat(chunks[0][0])).days == 60

    def test_year_window_subdivides_into_90_day_chunks(self):
        end = date(2026, 9, 9)
        start = end - timedelta(days=365)
        chunks = daily_chunks(start, end)
        assert len(chunks) == 5
        for a, b in chunks:
            span = (date.fromisoformat(b) - date.fromisoformat(a)).days
            assert 0 <= span <= 89
        assert chunks[0][0] == start.isoformat()
        assert chunks[-1][1] == end.isoformat()
        for (_, prev_b), (cur_a, _) in zip(chunks, chunks[1:]):
            assert (date.fromisoformat(cur_a) - date.fromisoformat(prev_b)).days == 1

    @pytest.mark.asyncio
    async def test_fetch_merges_chunks_and_dedups(self, monkeypatch):
        from app.core.evidence_cache import cache
        monkeypatch.setattr(cache, "get", _async_dict_get({}))
        stored = {}

        async def fake_merge(ticker, key, value, ttl=None):
            stored[ticker] = value

        monkeypatch.setattr(cache, "merge", fake_merge)

        calls = []

        async def fake_get(ticker: str, start: str | None = None, end: str | None = None) -> list:
            assert start is not None and end is not None
            calls.append((ticker, start, end))
            s = date.fromisoformat(start)
            e = date.fromisoformat(end)
            return [
                {"date": (s + timedelta(days=1)).isoformat(), "close": 100.0 + i, "volume": 1}
                for i in range((e - s).days - 1)
            ]

        monkeypatch.setattr("app.services.policy_signal.sectors_client.get_daily_transaction", fake_get)
        from app.services.policy_signal import fetch_daily_transaction

        data, hit = await fetch_daily_transaction("ADRO")
        assert hit is False
        assert data is not None
        assert len(calls) == 5
        assert stored["ADRO"] == data
        assert data[0]["date"] < data[-1]["date"]

    @pytest.mark.asyncio
    async def test_chunk_failure_raises_and_never_caches(self, monkeypatch):
        from app.core.evidence_cache import cache
        monkeypatch.setattr(cache, "get", _async_dict_get({}))
        stored = {}

        async def fake_merge(ticker, key, value, ttl=None):
            stored[ticker] = value

        monkeypatch.setattr(cache, "merge", fake_merge)

        async def fake_get(ticker, start=None, end=None):
            raise RuntimeError("boom")

        monkeypatch.setattr("app.services.policy_signal.sectors_client.get_daily_transaction", fake_get)
        from app.services.policy_signal import fetch_daily_transaction

        with pytest.raises(RuntimeError, match="boom"):
            await fetch_daily_transaction("ADRO")
        assert stored == {}


def _async_dict_get(env):
    async def get(ticker):
        return env.get(ticker)
    return get


def _counting_async(calls):
    async def inner(*_a, **_k):
        calls["n"] += 1
        return []
    return inner