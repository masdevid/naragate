import json

from app.models.schemas import Claim, NewsEvidence
from app.core.sectors_client import sectors_client
from app.core.evidence_cache import cache
from app.core.usage_tracker import record_sectors_cache_hit
from app.core import llm_client

NEWS_PROMPT = """You are a news corroboration analyst. Given a financial claim and recent news headlines
for the same company, determine whether the news supports, contradicts, or is neutral toward the claim.

Claim: {assertion} ({ticker})
Category: {category}
News headlines:
{headlines}

Return ONLY a JSON object with these fields:
- corroboration: one of "supports", "contradicts", "neutral"
- summary: a short 1-2 sentence summary in Indonesian explaining how the news relates to the claim
- summary_en: the same summary in English

Return ONLY valid JSON, no other text."""


class NewsAgent:
    async def analyze(self, claim: Claim) -> NewsEvidence:
        ticker = claim.ticker

        cached = await cache.get(ticker)
        if cached and "news_corpus" in cached:
            news_data = cached["news_corpus"]
            cache_hit = True
            record_sectors_cache_hit()
        else:
            news_data = await sectors_client.get_news(ticker, limit=10)
            await cache.merge(ticker, "news_corpus", news_data)
            cache_hit = False

        headlines = []
        if isinstance(news_data, dict):
            items = news_data.get("results") or news_data.get("data") or news_data.get("news") or news_data.get("items") or []
            if isinstance(items, list):
                for item in items[:10]:
                    if isinstance(item, dict):
                        headlines.append({
                            "title": item.get("title") or item.get("headline") or "",
                            "date": item.get("date") or item.get("published_at") or item.get("timestamp") or "",
                            "source": item.get("source") or item.get("publisher") or "",
                        })
        elif isinstance(news_data, list):
            for item in news_data[:10]:
                if isinstance(item, dict):
                    headlines.append({
                        "title": item.get("title") or item.get("headline") or "",
                        "date": item.get("date") or item.get("published_at") or item.get("timestamp") or "",
                        "source": item.get("source") or item.get("publisher") or "",
                    })

        corroboration = "no_news"
        summary = "Tidak ada berita terbaru untuk saham ini."
        summary_en = "No recent news for this stock."

        if headlines:
            headlines_str = json.dumps([h["title"] for h in headlines if h["title"]], ensure_ascii=False)
            prompt = NEWS_PROMPT.format(
                assertion=claim.assertion,
                ticker=ticker,
                category=claim.category.value,
                headlines=headlines_str[:1500],
            )

            try:
                raw = await llm_client.stream_chat(
                    "news",
                    [{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                result = llm_client.extract_json(raw) or {}
                corroboration = result.get("corroboration", "neutral")
                if corroboration not in ("supports", "contradicts", "neutral"):
                    corroboration = "neutral"
                summary = result.get("summary", summary)
                summary_en = result.get("summary_en", summary_en)
            except Exception:
                corroboration = "neutral"
                summary = "Berita tersedia tetapi tidak dapat dianalisis."
                summary_en = "News available but could not be analyzed."

        return NewsEvidence(
            claim_ticker=ticker,
            category="news",
            headlines=headlines,
            corroboration=corroboration,
            summary=summary,
            summary_en=summary_en,
            evidence_freshness=__import__("datetime").datetime.now().isoformat(),
            cache_hit=cache_hit,
        )


news_agent = NewsAgent()