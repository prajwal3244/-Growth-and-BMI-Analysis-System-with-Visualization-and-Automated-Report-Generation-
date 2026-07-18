# Architecture

GrowthAI is a layered **Clean Architecture** application. Diagrams below use Mermaid and
render natively on GitHub.

## Component / container diagram

```mermaid
flowchart TB
    subgraph Interfaces
        ST[Streamlit Dashboard]
        API[FastAPI + Swagger]
    end
    subgraph Services
        GS[GrowthService]
        NS[NutritionService]
        RS[RiskService]
        RPS[ReportService]
        CB[ChatService / RAG]
    end
    subgraph Domain
        CORE[core: bmi, domain, z-scores]
        ML[ml: forecast, explain]
        DATA[data: WHO/CDC/IAP reference]
        VIZ[viz: Plotly charts]
    end
    subgraph Infra
        DB[(SQLAlchemy DB)]
        KB[(WHO knowledge base)]
    end

    ST --> API
    ST --> GS & NS & RS & RPS & CB
    API --> GS & NS & RS & RPS & CB
    GS --> CORE & DATA & ML
    NS --> CORE & DATA
    RS --> CORE & DATA & ML
    RPS --> VIZ & CORE
    CB --> KB
    API --> DB
```

## Sequence — full analysis request

```mermaid
sequenceDiagram
    actor Parent
    participant ST as Streamlit
    participant API as FastAPI
    participant GS as GrowthService
    participant ML as ML Forecaster
    participant NS as NutritionService
    participant RS as RiskService
    participant DB as Database

    Parent->>ST: Enter age, gender, height, weight
    ST->>API: POST /analysis (JWT)
    API->>GS: analyze(measurement)
    GS->>GS: BMI + z-score + percentile (WHO/CDC/IAP)
    GS->>ML: forecast(+6mo, +1yr)
    ML-->>GS: predictions + confidence + feature importance
    API->>NS: recommend(profile)
    API->>RS: assess(profile, forecast)
    RS-->>API: risk scores + explanations
    API->>DB: persist patient, measurement, prediction
    API-->>ST: analysis payload
    ST-->>Parent: cards, Plotly charts, PDF, chatbot
```

## Entity-Relationship diagram

```mermaid
erDiagram
    USER ||--o{ PATIENT : manages
    PATIENT ||--o{ MEASUREMENT : has
    MEASUREMENT ||--o| ANALYSIS : produces
    ANALYSIS ||--o{ PREDICTION : contains
    PATIENT ||--o{ REPORT : generates
    PATIENT ||--o{ MEALPLAN : receives

    USER {
        int id PK
        string email
        string hashed_password
        string role
        datetime created_at
    }
    PATIENT {
        int id PK
        int user_id FK
        string name
        string gender
        date birth_date
    }
    MEASUREMENT {
        int id PK
        int patient_id FK
        float age_months
        float height_cm
        float weight_kg
        datetime taken_at
    }
    ANALYSIS {
        int id PK
        int measurement_id FK
        float bmi
        string category
        float z_score
        float percentile
        string standard
    }
    PREDICTION {
        int id PK
        int analysis_id FK
        string horizon
        float height_cm
        float weight_kg
        float bmi
        float confidence
    }
```

## Class diagram — domain core

```mermaid
classDiagram
    class Gender { <<enum>> MALE FEMALE }
    class Standard { <<enum>> WHO CDC IAP }
    class BmiCategory { <<enum>> UNDERWEIGHT NORMAL OVERWEIGHT OBESE }
    class Measurement {
        +float age_months
        +float height_cm
        +float weight_kg
        +Gender gender
        +bmi() float
    }
    class GrowthAssessment {
        +float bmi
        +BmiCategory category
        +float z_score
        +float percentile
        +Standard standard
    }
    class ReferenceDataService {
        +median(gender, age, metric) float
        +z_score(...) float
        +percentile(...) float
    }
    Measurement --> Gender
    GrowthAssessment --> BmiCategory
    GrowthAssessment --> Standard
    ReferenceDataService --> Standard
```

## Technology choices

| Concern | Choice | Rationale |
| --- | --- | --- |
| Backend | FastAPI + Pydantic v2 | Async, typed, auto Swagger, industry standard |
| ORM | SQLAlchemy 2.0 | Works with SQLite (dev) and Postgres (prod) |
| ML | scikit-learn | RF/GBR/LinReg, transparent, no GPU needed |
| Explainability | feature importance + optional SHAP | Trust & transparency for health predictions |
| Charts | Plotly | Interactive, exportable, embeds in web + PDF |
| Dashboard | Streamlit | Fast, pure-Python, ideal for ML/health UIs |
| Chatbot | LangChain-style offline RAG | Works with zero API keys; pluggable LLM |
| Reports | Jinja2 + WeasyPrint | Preserves original pipeline, upgraded template |
| Auth | JWT (python-jose) + passlib | Stateless, standard |
| Packaging | pyproject (PEP 621) | Installable `pip install -e .` |
| Delivery | Docker, docker-compose, GitHub Actions | One-command run, CI on every push |
