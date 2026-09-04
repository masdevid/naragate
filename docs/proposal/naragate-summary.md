# Naragate — ChatGPT Summary

## Core idea

The proposed hackathon project is an AI system that detects financial claims in Indonesian market narratives and tests those claims against actual financial reality using Sectors data.

Instead of a generic sentiment model, the product asks: _How strongly does the available financial evidence support or contradict the claim?_ This turns the project into a market-intelligence and evidence-validation tool rather than a simple news summarizer.

## Why Sectors is central

Sectors is the core data source for the product. The idea depends on Sectors to provide the factual ground truth for valuation, fundamentals, market performance, and narrative comparison.

Key points from the discussion:

- Normal Sectors API access is tied to the Sectors Insider plan.
- Hackathon teams receive a grant of 1,000 Sectors API credits for the competition project.
- Each team member needs to create a Sectors account and complete onboarding.
- The team representative claims the 1,000-credit grant from the hackathon portal.
- The grant is for the hackathon project and should be treated as demo-budgeted rather than unlimited access.

## Important product direction

The discussion suggests a strong correction to the original approach:

- Do not waste credits querying every stock every day.
- Build around a narrow, high-value subset of companies and claims.
- Prioritize quality and demonstrable evidence over raw scale.
- Focus on a few carefully selected stocks and narratives to make the prototype compelling and credible.

This is especially important because the judging is about the quality of the working product, not the volume of calls made.

## Sectors v2 is the target

The conversation emphasizes that the supported current version is Sectors v2, and v1 has been discontinued.

The product should be built against:

- Company report endpoints
- Quarterly financial data
- Subsector reports
- Daily transaction data
- News data

The recommendation is to use only the exact sections needed for a claim rather than fetching broad, unnecessary payloads.

## Key data families the system actually needs

The project can be built around five core evidence families:

1. Valuation claims
   - PE, PB, PS, PCF
   - Used to verify claims like “this stock is expensive” or “this stock is cheap”

2. Fundamental claims
   - Revenue, earnings, EPS, margins, ROE, ROA, debt metrics
   - Used to evaluate claims like “earnings are falling” or “profitability is improving”

3. Peer and subsector comparison
   - Peer median valuations and subsector metrics
   - Used to compare the target stock relative to its peers

4. Market performance claims
   - Daily price and volume movement
   - Used for claims like “the stock is crashing” or “it is surging”

5. News / narrative corpus
   - Narrative context from Sectors news dataset
   - Used to detect and classify emotional or rhetorical claims

## Core endpoints to use

### 1) Company Report
This is the primary workhorse endpoint.

Useful sections include:

- valuation
- financials
- peers
- overview
- dividend
- future
- ownership
- management

Examples:

- “BBCA is too expensive” → use valuation metrics
- “BBRI earnings keep falling” → use financials and growth metrics
- “BBRI is cheaper than other banks” → compare peer metrics

### 2) Quarterly Financials
This is especially important for temporal reasoning.

It allows the system to distinguish:

- “profit fell”
- “profit has fallen continuously”

This supports a more nuanced verdict such as SUPPORTED, PARTIALLY SUPPORTED, or MIXED.

### 3) Subsector Report
This acts as the “reality context” layer.

It helps answer whether a company is truly expensive or cheap relative to its sector median.

Example:

- BBRI PE = 14.2x
- Banking subsector median PE = 11.7x
- Premium = +21.4%

This makes the evaluation quantitative rather than impressionistic.

### 4) Daily Transaction
This covers market-performance claims.

Example:

- “BBRI is collapsing” can be assessed across 1D, 7D, and 30D performance windows.

This is useful because Indonesian market narratives often use emotionally loaded terms such as:

- anjlok
- jeblok
- meledak
- meroket
- mahal
- murah

### 5) News
The discussion argues that Sectors news may let the team avoid building an external scraper for the MVP.

The news dataset can provide:

- title and body
- source
- ticker associations
- tags and dimensions such as valuation, financials, management, or ownership

This creates a strong narrative-to-evidence pipeline.

## Proposed architecture

A practical architecture would be:

- Narrative input from user or news feed
- Claim extraction
- Claim classification into valuation, fundamental, or market categories
- Evidence engine querying Sectors
- Counter-evidence and skepticism layer
- Reality Gap scoring
- Verdict with reasoning

The system is more compelling if it is designed as a skeptical verifier:

- Instead of “Give me an analysis of BBRI”
- Use “Here is a claim. Try to prove it wrong.”

This is a much more defensible and technically stronger product story.

## Reality Gap score

The discussion proposes scoring how strongly the evidence agrees with the narrative.

Example:

- Claim: “BBCA is too expensive.”
- Evidence: PE and PB far above peer median
- Result: HIGH evidence strength, large Reality Gap score

Another example:

- Claim: “BBRI earnings are collapsing.”
- Evidence: revenue and earnings still positive, though growth slowed
- Result: MIXED or PARTIALLY SUPPORTED, not outright supported

The score is not a buy/sell recommendation; it measures how aligned the narrative is with the underlying financial reality.

## Multi-agent lens

The earlier multi-agent work can be adapted without copying the old project wholesale.

Suggested specialization:

- Claim Parser
- Valuation Agent
- Fundamental Agent
- Market Agent
- Skeptic Agent
- Evidence Judge
- Reality Gap Score Generator

The Skeptic Agent is particularly valuable because it tries to disprove the claim, increasing robustness and making the system feel like a serious research assistant rather than a generic LLM summary tool.

## Estimated API usage and credit budget

The discussion explicitly notes that exact per-endpoint credit costs are not publicly documented, so the estimates are approximate assuming roughly 1 credit per request.

### Per claim package estimate

A single claim package may require roughly 4 API calls:

- Company report — valuation
- Company report — financials
- Subsector report
- Quarterly financials

This implies:

- 4 calls per claim package
- 1,000 credits / 4 ≈ 250 claim packages

That is enough for a solid demo.

### More realistic planned budget

A strong budget allocation would look roughly like this:

- Initial company universe/discovery: 10
- Subsector metadata: 10
- Company evidence cache: 100
- Quarterly evidence: 100
- Peer/subsector evidence: 50
- News corpus: 100
- Demo/testing: 100
- Buffer: 530

Total: roughly 470–500 calls, leaving a comfortable cushion.

This suggests the product can be built safely within the 1,000-credit grant, provided the system uses a cache and avoids repeated unnecessary queries.

## Best product framing for the hackathon

The best framing is not:

> “AI that checks whether financial discussions are positive or negative.”

It is:

> “Naragate: an evidence engine that detects financial claims in Indonesian market narratives and tests them against Sectors’ financial reality.”

That is easy to explain in under 3 minutes and maps directly to the competition’s market-intelligence themes.

## Final recommendation

The strongest path is to build a focused MVP around a few high-visibility Indonesian stocks and a small set of claims categories:

- valuation
- fundamentals
- market performance
- peer comparison

Then use Sectors v2 as the factual verification layer and produce a credibility score that explains why the narrative is supported, contradicted, or mixed.

This is a much stronger hackathon submission than a generic AI assistant because it is a real evidence engine tied directly to market truth.

## One caution

The discussion warns not to hard-code exact endpoint schemas before validating the current docs. Some search results may still show legacy v1 references, but the public documentation confirms that v2 is the active version and should be the implementation target.
