# Naragate — Mermaid Diagrams

## 1) High-level system architecture

```mermaid
flowchart TD
    A[Market narrative / news / user claim] --> B[Claim extraction]
    B --> C[Claim classification]
    C --> D{Claim type}

    D -->|Valuation| E[Company Report + Subsector Report]
    D -->|Fundamental| F[Company Report + Quarterly Financials]
    D -->|Market| G[Daily Transaction + News]
    D -->|Peer comparison| H[Subsector Report + Company Report]

    E --> I[Evidence normalization]
    F --> I
    G --> I
    H --> I

    I --> J[Skeptic / counter-evidence analysis]
    J --> K[Reality Gap score]
    K --> L[Supported / Mixed / Contradicted verdict]
    L --> M[Explainable evidence summary]
```

## 2) Claim-to-evidence workflow

```mermaid
sequenceDiagram
    participant U as User / News Input
    participant P as Claim Parser
    participant C as Classifier
    participant S as Sectors API
    participant E as Evidence Engine
    participant J as Judge
    participant R as Reality Gap Score

    U->>P: Narrative statement
    P->>C: Extract structured claim
    C->>S: Route to relevant endpoints
    S-->>E: Raw financial data
    E->>J: Normalize and compare metrics
    J->>R: Compute evidence alignment
    R-->>U: Verdict + explanation
```

## 3) Multi-agent design

```mermaid
flowchart LR
    A[Input narrative] --> B[Claim Parser]
    B --> C[Valuation Agent]
    B --> D[Fundamental Agent]
    B --> E[Market Agent]

    C --> F[Evidence Judge]
    D --> F
    E --> F

    F --> G[Skeptic Agent]
    G --> H[Reality Gap Score Generator]
    H --> I[Final verdict + rationale]
```

## 4) Evidence validation pattern

```mermaid
flowchart TD
    A[Claim: "BBRI labanya jeblok"] --> B[Classify claim]
    B --> C[Fetch quarterly financials]
    B --> D[Fetch company report]
    B --> E[Fetch peer & subsector benchmark]

    C --> F[Assess earnings trend]
    D --> G[Assess profitability metrics]
    E --> H[Assess relative valuation]

    F --> I[Aggregate evidence]
    G --> I
    H --> I

    I --> J{Does data support claim?}
    J -->|Yes| K[Supported]
    J -->|Partially| L[Mixed / Partially supported]
    J -->|No| M[Contradicted]
```

## 5) Data source mapping

```mermaid
flowchart TB
    N[Narrative claim] --> X[Claim extraction]
    X --> A1[Company Report]
    X --> A2[Quarterly Financials]
    X --> A3[Subsector Report]
    X --> A4[Daily Transaction]
    X --> A5[News Corpus]

    A1 --> B[Valuation + Fundamentals]
    A2 --> B
    A3 --> B
    A4 --> B
    A5 --> B

    B --> C[Reality Gap assessment]
    C --> D[Explainable verdict]
```

## 6) Score computation logic

```mermaid
flowchart TD
    A[Claim statement] --> B[Metric extraction]
    B --> C[Peer/subsector benchmark]
    B --> D[Historical trend analysis]
    B --> E[Price / volume context]

    C --> F[Relative evidence score]
    D --> G[Trend evidence score]
    E --> H[Market evidence score]

    F --> I[Composite evidence score]
    G --> I
    H --> I

    I --> J[Confidence + contradiction analysis]
    J --> K[Reality Gap score out of 100]
    K --> L[Final verdict]
```

## 7) MVP architecture for hackathon demo

```mermaid
flowchart LR
    A[Dashboard / Web app] --> B[Claim input]
    B --> C[Backend API]
    C --> D[Claim parser + classifier]
    D --> E[Evidence cache]
    D --> F[Sectors v2 client]
    E --> G[Scoring engine]
    F --> G
    G --> H[Result card]
    H --> I[Supported / Mixed / Contradicted]
    I --> J[Explanation panel]
```
