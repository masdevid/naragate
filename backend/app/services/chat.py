import json

from app.core import llm_client

CHAT_PROMPT = """You are Naragate's analyst assistant. A user ran a Reality Gap analysis on a market narrative
and now asks a follow-up question. Answer using ONLY the evidence below. Be concise and honest.
If the evidence does not answer the question, say so.

Claim: {assertion} ({ticker})
Category: {category}
Narrative: {narrative}
Evidence: {evidence}
Score: {score}/100 ({verdict})
Skeptic notes: {skeptic}

Question: {question}

Return ONLY a JSON object with these fields:
- answer: the answer in Indonesian (1-3 sentences)
- answer_en: the same answer in English

Return ONLY valid JSON, no other text."""


async def answer_followup(claim_state: dict, question: str) -> dict:
    claim = claim_state.get("claim") or {}
    evidence = claim_state.get("evidence") or {}
    score = claim_state.get("score") or {}
    skeptic = claim_state.get("skeptic") or {}

    evidence_str = json.dumps(evidence, default=str, indent=2)[:2000]
    skeptic_str = json.dumps(skeptic, default=str, indent=2)[:800]

    prompt = CHAT_PROMPT.format(
        assertion=claim.get("assertion", ""),
        ticker=claim.get("ticker", ""),
        category=claim.get("category", ""),
        narrative=claim_state.get("narrative", ""),
        evidence=evidence_str,
        score=score.get("reality_gap_score", "?"),
        verdict=score.get("verdict", "?"),
        skeptic=skeptic_str,
        question=question,
    )

    try:
        raw = await llm_client.stream_chat(
            "chat",
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        result = llm_client.extract_json(raw) or {}
        return {
            "answer": result.get("answer", "Tidak dapat menjawab pertanyaan ini."),
            "answer_en": result.get("answer_en", "Unable to answer this question."),
        }
    except Exception:
        return {
            "answer": "Tidak dapat menjawab pertanyaan ini berdasarkan bukti yang tersedia.",
            "answer_en": "Unable to answer this question based on available evidence.",
        }