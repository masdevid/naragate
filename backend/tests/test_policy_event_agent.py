import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.policy_event_agent import (
    label_policy_events,
    headlines_from_sector_evidence,
    extract_policy_events_from_sector,
)


class TestLabelPolicyEvents:
    def test_labels_subsidy_headline_with_actor_and_keyword(self):
        headlines = [{
            "title": "Pemerintah umumkan subsidi BBM dinaikkan",
            "date": "2026-02-03",
            "source": "Kompas",
        }]
        events = label_policy_events(headlines, sector="oil-gas")
        assert len(events) == 1
        ev = events[0]
        assert ev["date"] == "2026-02-03"
        assert ev["actor"] == "pemerintah"
        assert ev["keyword"] == "subsidi bbm"

    def test_pertamina_actor_recognized(self):
        headlines = [{
            "title": "Pertamina siapkan harga bbm baru",
            "date": "2026-01-15",
        }]
        events = label_policy_events(headlines, sector="oil-gas")
        assert events[0]["actor"] == "pertamina"
        assert events[0]["keyword"] == "harga bbm"

    def test_coal_hba_keyword(self):
        headlines = [{
            "title": "HBA turun bulan ini",
            "date": "2026-03-01",
        }]
        events = label_policy_events(headlines, sector="coal")
        assert len(events) == 1
        assert events[0]["keyword"] == "hba"

    def test_unrelated_headline_yields_no_event(self):
        headlines = [{"title": "Cuaca cerah di Jakarta", "date": "2026-01-01"}]
        events = label_policy_events(headlines, sector="coal")
        assert events == []

    def test_empty_headlines_no_crash(self):
        assert label_policy_events([]) == []
        assert label_policy_events(None) == []

    def test_actor_absent_becomes_none(self):
        events = label_policy_events([{"title": "kenaikan harga minyak", "date": "2026-02-01"}], sector="oil-gas")
        assert events[0]["actor"] is None
        assert events[0]["keyword"] == "minyak"

    def test_longest_keyword_wins(self):
        events = label_policy_events([{"title": "subsidi bbm berkurang", "date": "2026-01-01"}], sector="oil-gas")
        assert events[0]["keyword"] == "subsidi bbm"

    def test_fallback_sector_uses_star_keywords(self):
        events = label_policy_events([{"title": "tarif naik", "date": "2026-01-01"}], sector="unlisted-sector")
        assert events[0]["keyword"] == "tarif"


class TestExtractFromSectorEvidence:
    def test_flattens_member_news_headlines(self):
        sector_evidence = {
            "sector": "oil-gas",
            "by_member": {
                "PGAS": {"news": {"headlines": [
                    {"title": "Pemerintah naikkan subsidi BBM", "date": "2026-02-03"},
                ]}},
                "MEDC": {"news": {"headlines": [
                    {"title": "Medco kuartal bagus", "date": "2026-01-01"},
                ]}},
            },
        }
        headlines = headlines_from_sector_evidence(sector_evidence)
        assert len(headlines) == 2

    def test_extract_events_from_sector(self):
        sector_evidence = {
            "sector": "oil-gas",
            "by_member": {
                "PGAS": {"news": {"headlines": [
                    {"title": "Pemerintah umumkan subsidi bbm naik", "date": "2026-02-03"},
                ]}},
            },
        }
        events = extract_policy_events_from_sector(sector_evidence, "oil-gas")
        assert len(events) == 1
        assert events[0]["keyword"] == "subsidi bbm"
        assert events[0]["actor"] == "pemerintah"

    def test_no_related_news_yields_empty_list(self):
        sector_evidence = {
            "sector": "coal",
            "by_member": {"ADRO": {"news": {"headlines": [
                {"title": "ADRO rilis laporan keuangan", "date": "2026-01-01"},
            ]}}},
        }
        assert extract_policy_events_from_sector(sector_evidence, "coal") == []

    def test_empty_evidence_no_crash(self):
        assert extract_policy_events_from_sector({}, "coal") == []
        assert extract_policy_events_from_sector(None, "coal") == []


class TestPipelinePolicyEventLabeling:
    @pytest.mark.asyncio
    async def test_policy_event_labeled_event_emitted(self):
        from app.services.pipeline import run_pipeline
        from app.core import llm_client

        mock_store = MagicMock()
        mock_store.create_claim = AsyncMock(return_value="test-claim")
        mock_store.update_claim = AsyncMock()
        mock_store.find_active_by_narrative = AsyncMock(return_value=None)
        mock_store.get_claim = AsyncMock(return_value=None)

        llm_response = '{"ticker": "UNKNOWN", "category": "market", "assertion": "batu bara naik", "direction": "above", "confidence": 0.8}'
        sector_evidence = {
            "sector": "coal",
            "members": ["ADRO"],
            "by_member": {"ADRO": {"news": {"headlines": [
                {"title": "Pemerintah tetapkan hba baru", "date": "2026-03-01"},
            ]}}},
            "fetched_at": "2026-03-01",
        }
        with patch.object(llm_client, "stream_chat", new_callable=AsyncMock) as mock_llm, \
             patch("app.services.pipeline.claims_store", mock_store), \
             patch("app.services.pipeline.sectors_client.validate_ticker_exists", new_callable=AsyncMock) as exists, \
             patch("app.services.pipeline.get_sector_evidence", new_callable=AsyncMock) as mock_gse:
            mock_llm.return_value = llm_response
            exists.return_value = True
            mock_gse.return_value = sector_evidence

            events = []
            async for ev in run_pipeline("Harga batu bara naik"):
                events.append(ev)

        types = [e.event_type for e in events]
        assert "policy_event_labeled" in types
        labeled = next(e.data for e in events if e.event_type == "policy_event_labeled")
        assert len(labeled["policy_events"]) == 1
        ev = labeled["policy_events"][0]
        assert ev["keyword"] == "hba"
        assert ev["actor"] == "pemerintah"
        assert ev["date"] == "2026-03-01"