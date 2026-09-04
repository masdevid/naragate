# Naragate — Technical Overview

## Goal

Build an AI-powered evidence engine that reads Indonesian market narratives and determines whether the claim matches financial reality, using Sectors as the source of truth.

The product is not just sentiment analysis. It is a verification system that classifies financial claims, retrieves evidence, compares them to objective market data, and returns a confidence-based verdict.

## Core product idea

Input:
- A narrative statement such as “BBRI labanya jeblok”
- Or a headline/news item describing a stock or sector

Process:
1. Extract the claim
2. Classify the claim type
   - valuation
   - fundamental
   - market performance
   - peer/subsector comparison
3. Retrieve relevant Sectors data
4. Compare the narrative against financial metrics
5. Produce a structured verdict and evidence summary

Output:
- Supported
- Partially supported
- Mixed
- Contradicted
- With a “Reality Gap” score and explanation

## System architecture

The architecture can be modeled as a pipeline:

- User or news feed
  -> Claim extraction
  -> Claim classification
  -> Evidence retrieval from Sectors
  -> Cross-checking and counter-evidence
  -> Reality Gap scoring
  -> Final verdict

A more advanced version uses specialized agents:

- Claim Parser
- Valuation Agent
- Fundamental Agent
- Market Agent
- Skeptic Agent
- Evidence Judge
- Reality Gap Score Generator

The key idea is epistemic specialization: each agent is responsible for a specific type of reasoning, and the Skeptic Agent actively tries to disprove the original claim instead of blindly validating it.

## Data sources

The project is anchored on Sectors v2 endpoints.

### 1. Company report
Primary source for company-level truth.

Use sections such as:
- valuation
- financials
- peers
- overview
- dividend
- management
- ownership

This covers claims like:
- “BBCA too expensive”
- “BBRI earnings are deteriorating”
- “BBRI is cheaper than peer banks”

### 2. Quarterly financials
Critical for temporal analysis.

This allows the system to detect whether an earnings trend is actually worsening over time rather than relying on a single snapshot.

### 3. Subsector report
Provides contextual comparison within the sector.

Helps answer:
- Is the stock expensive relative to peers?
- Is the company outperforming or underperforming its subsector?

### 4. Daily transaction data
For market-performance claims such as:
- “Stock is crashing”
- “Stock is rising sharply”

The system can compare short-term and medium-term moves across windows like 1D, 7D, and 30D.

### 5. News data
Useful for ingesting narrative context without building a custom scraper in the MVP.

Can provide:
- article title/body
- source metadata
- ticker associations
- tags and topic dimensions

## Claim model

The system should convert fuzzy market language into explicit financial statements.

Examples:
- “mahal” -> valuation premium above peer median
- “jeblok” -> earnings or margin deterioration
- “anjlok” -> negative price change over a time window
- “meroket” -> strong price or revenue growth

This translation step is essential because the value of the system is in testing structured financial propositions instead of doing generic sentiment classification.

## Evidence engine

The evidence engine is the main technical component.

It should:
- map a claim to one or more Sectors data families
- request only the required sections
- normalize metrics across time and peers
- compute relative comparisons with the sector or peer group
- detect contradictory evidence
- calculate a confidence score for the verdict

Example:
- Claim: “BBRI sudah murah”
- Evidence: BBRI PE is below peer median and valuation is favorable
- Result: supported if the numbers align

Example:
- Claim: “BBRI labanya jeblok”
- Evidence: revenue and earnings remain positive, though growth slowed
- Result: mixed or partially supported

## Reality Gap scoring

The scoring model is designed to answer:

“How strongly does the narrative line up with the financial reality?”

It is not a buy/sell score. It is a consistency score.

Possible dimensions:
- valuation gap
- earnings gap
- market momentum gap
- peer relative gap
- evidence confidence

A final score could be represented on a 0–100 scale with a verdict band:
- 0–30: contradicted
- 31–60: mixed / partially supported
- 61–80: supported
- 81–100: strongly supported

## API usage strategy

The discussion stresses cost control.

The team should avoid:
- querying every stock every day
- fetching broad data for all companies in the universe
- repeatedly calling the same endpoints without caching

Instead:
- target a curated set of companies
- cache evidence locally
- process claims in batches
- reuse peer and sector snapshots
- maintain a small evidence graph per stock

A realistic estimate is roughly 4 calls per claim package, so 1,000 credits can cover a meaningful MVP if the system is disciplined.

## MVP design

A good MVP would focus on a small but high-signal stock universe and a few claim categories:

- valuation
- fundamentals
- peer comparison
- market movement

This makes the demo clearer and more compelling than a broad but shallow search across many stocks.

## Why this is a strong hackathon project

This project differentiates itself from a generic AI financial assistant because it is:

- evidence-grounded
- quantitative
- skeptical by design
- tied to a real market-data source
- interpretable through structured reasoning

It turns narrative analysis into a measurable, auditable output, which is a strong fit for a product-oriented hackathon demo.

## Final technical framing

The most compelling framing is:

> An evidence engine that detects financial claims in Indonesian market narratives and verifies them against Sectors’ financial reality.

This is more defensible than “AI sentiment analysis” because it is grounded in actual company and sector data, uses an explicit claim-to-evidence pipeline, and produces explainable conclusions rather than generic summaries.
