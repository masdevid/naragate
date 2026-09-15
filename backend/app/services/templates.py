"""Curated demo narrative templates.

Single source of truth for the 12 example narratives shown as tiles in the web
dashboard and returned to non-web clients (MCP) so every surface offers the same
entry points. Kept in sync with the frontend i18n strings
(`dashboard.examples.*`); prefer adding here first and mirroring in i18n.
"""

TEMPLATES: list[dict] = [
    {
        "id": "valuation",
        "category": "valuation",
        "label": "Valuasi",
        "label_en": "Valuation",
        "narrative": "PE BBCA mahal di 25x, jauh di atas rata-rata sektor 18x.",
        "narrative_en": "BBCA PE is expensive at 25x, far above the sector average of 18x.",
    },
    {
        "id": "fundamental",
        "category": "fundamental",
        "label": "Fundamental",
        "label_en": "Fundamental",
        "narrative": "Pendapatan TLKM terus tumbuh tapi laba bersihnya menyusut setiap kuartal.",
        "narrative_en": "TLKM revenue keeps growing but net profit is shrinking every quarter.",
    },
    {
        "id": "market",
        "category": "market",
        "label": "Pasar",
        "label_en": "Market",
        "narrative": "Saham UNVR turun 15% dalam seminggu, investor panik.",
        "narrative_en": "UNVR stock has dropped 15% in a week, investors are panicking.",
    },
    {
        "id": "news",
        "category": "news",
        "label": "Berita",
        "label_en": "News",
        "narrative": "BMRI disebut bank terbaik di Indonesia saat ini setelah berita laba rekor.",
        "narrative_en": "BMRI is being called the best bank in Indonesia right now after record profit news.",
    },
    {
        "id": "policy_bbm",
        "category": "policy",
        "label": "Kebijakan · BBM",
        "label_en": "Policy · BBM",
        "narrative": "Subsidi BBM dipangkas — harga BBM bersubsidi naik kuartal ini.",
        "narrative_en": "The BBM fuel subsidy is being cut — subsidized prices rise this quarter.",
    },
    {
        "id": "policy_hba",
        "category": "policy",
        "label": "Kebijakan · HBA",
        "label_en": "Policy · HBA",
        "narrative": "HBA batu bara ditetapkan naik untuk Q3 — untung ADRO ikut naik.",
        "narrative_en": "Coal reference price HBA is set higher for Q3 — ADRO profits follow.",
    },
    {
        "id": "policy_nickel",
        "category": "policy",
        "label": "Kebijakan · Nikel",
        "label_en": "Policy · Nickel",
        "narrative": "Larangan ekspor bijih nikel diperketat — INCO untung dari hilirisasi.",
        "narrative_en": "Nickel ore export ban tightened — INCO gains from downstreaming.",
    },
    {
        "id": "no_ticker",
        "category": "edge",
        "label": "Butuh kode",
        "label_en": "Needs ticker",
        "narrative": "Saham perbankan sedang mahal.",
        "narrative_en": "Banking stocks are expensive.",
    },
    {
        "id": "contradiction",
        "category": "contradiction",
        "label": "Kontradiksi",
        "label_en": "Contradiction",
        "narrative": "Laba BBRI naik tapi sahamnya terus turun 20% bulan ini.",
        "narrative_en": "BBRI profit grows but its stock keeps falling 20% this month.",
    },
    {
        "id": "future_price",
        "category": "future_price",
        "label": "Harga masa depan",
        "label_en": "Future price",
        "narrative": "Harga saham BBCA akan berlipat tahun ini.",
        "narrative_en": "BBCA shares will double this year.",
    },
    {
        "id": "below_cpo",
        "category": "below",
        "label": "Turun",
        "label_en": "Below",
        "narrative": "Harga CPO turun — laba AALI tertekan.",
        "narrative_en": "CPO prices are falling — AALI profits are under pressure.",
    },
    {
        "id": "below_auto",
        "category": "below",
        "label": "Turun",
        "label_en": "Below",
        "narrative": "Penjualan mobil melemah kuartal ini — pendapatan ASII akan merosot.",
        "narrative_en": "Auto sales are weak this quarter — ASII revenue will slide.",
    },
]
