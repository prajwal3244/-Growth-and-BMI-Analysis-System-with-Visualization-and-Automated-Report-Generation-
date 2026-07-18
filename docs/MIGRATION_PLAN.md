# Migration Plan — From Script to Platform

This document is the honest, senior-engineer migration plan for evolving the original
single-file `GrowthInsight.py` into **GrowthAI**, a production-grade, open-source AI
health-intelligence platform.

> **Guiding principle:** *Refactor, don't rewrite.* Every capability of the original
> script is preserved and improved, never discarded. The original is kept verbatim in
> [`legacy/GrowthInsight_original.py`](../legacy/GrowthInsight_original.py) for provenance.

---

## 1. What the original did (and its problems)

| Original capability | Where it lived | Kept as |
| --- | --- | --- |
| Read WHO/CDC growth CSV (male/female) | `pd.read_csv(...)` | `growthai.data.reference.ReferenceDataService` |
| BMI = weight / height² | `calculate_bmi()` | `growthai.core.bmi.calculate_bmi()` |
| BMI classification | `determine_bmi_category()` | `growthai.core.bmi.classify_bmi()` (fixed + child-aware) |
| Charts | matplotlib pie/line | `growthai.viz.charts` (Plotly, interactive) |
| PDF report | Jinja2 + WeasyPrint | `growthai.reports.pdf` (hospital-grade template) |

### Real defects found in the original (now fixed)

1. **~90 lines duplicated** between the male and female branches → collapsed to one code path.
2. **`f"{height:1f}"`** (lines 54, 133) — missing the dot; never formatted correctly → `:.1f`.
3. **Classification gaps** — `24.9–25.0` and `29.9–30.0` fell through to "Obesity" → boundaries fixed.
4. **Adult BMI cut-offs applied to children** — clinically wrong; the whole point of the CSV
   (age reference) was ignored → replaced with **age/gender-aware z-score classification**.
5. **`age` compared as raw string** (`"5Years"`) against messy CSV → robust age parser
   (`0Months`…`20Years` → months).
6. **Blocking `input()` / `plt.show()`** — unusable as a service → pure functions + service layer.

---

## 2. Target architecture (Clean Architecture)

```
             ┌───────────────────────────────────────────────┐
             │                 Interfaces                     │
             │   Streamlit dashboard   │   FastAPI + Swagger  │
             └───────────────┬───────────────────┬───────────┘
                             │                   │
             ┌───────────────▼───────────────────▼───────────┐
             │                  Services                      │
             │ growth · nutrition · risk · report · chatbot   │
             └───────────────┬───────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐        ┌────────────┐       ┌────────────┐
   │  core   │        │    ml      │       │    data    │
   │ bmi,    │        │ forecast,  │       │ reference  │
   │ domain  │        │ explain    │       │ WHO/CDC/IAP│
   └─────────┘        └────────────┘       └────────────┘
        │                    │                    │
        └──────────► db (SQLAlchemy) / viz (Plotly) ◄────────
```

Dependencies point **inward**: `core` depends on nothing; `services` orchestrate `core`,
`ml`, `data`; interfaces depend on `services`. This keeps the domain logic testable and
framework-free (SOLID / Dependency Inversion).

---

## 3. Phased delivery

Each phase ships **production-ready, runnable** code — no stubs. Phases are ordered so the
platform is demonstrable end-to-end as early as possible.

| Phase | Theme | Ships | Why / Impact |
| --- | --- | --- | --- |
| **0** | Foundation | Repo structure, config, logging, packaging, preserved legacy | Turns a script into a maintainable, installable product; unblocks everything |
| **1** | Core domain | Enums, fixed BMI, reference-data engine (WHO/CDC/IAP switch), z-scores | Clinically correct core; reuses & fixes original logic |
| **2** | AI growth prediction | RF / GradientBoosting / LinearRegression comparison, 6-month & 1-year forecast, explainability | The "AI" that separates this from a calculator; recruiter-visible ML |
| **3** | Nutrition & risk intelligence | Calorie/macro/water/sleep/activity engine, meal plans, multi-risk scoring with explanations | Actionable health guidance; explainable, WHO-aligned |
| **4** | Visualization & reports | Plotly gauge/radar/timeline/percentile, hospital-grade PDF with QR | Interactive, research-ready; strong visual portfolio signal |
| **5** | AI assistant | Offline RAG chatbot over WHO guidelines + pluggable LLM adapter | Always-works AI assistant, no API key required |
| **6** | Backend API | FastAPI, SQLAlchemy, JWT auth, Swagger, CRUD | Real production backend; API-first design |
| **7** | Dashboard | Streamlit multi-page app: dark mode, cards, charts, analytics | The face of the product; the demo recruiters click |
| **8** | Quality & delivery | Pytest suite, Docker, docker-compose, GitHub Actions CI, docs, diagrams | Proves engineering maturity; one-command run |
| **9** | Future scope | React frontend, wearable/IoT integration, mobile | Documented roadmap; shows product vision |

Phases 0–8 are implemented in this repository. Phase 9 is documented in
[`ROADMAP.md`](./ROADMAP.md).

---

## 4. Backward compatibility

- The original CSVs are preserved at the repo root **and** normalized copies live in
  `datasets/who/`. The reference engine reads either.
- The original PDF template is upgraded but the Jinja2 + WeasyPrint pipeline is retained.
- `legacy/GrowthInsight_original.py` runs exactly as before for anyone who wants the old CLI.

---

## 5. How each phase is verified

Every phase adds tests under `tests/`. `make test` runs the suite; `make run-api` and
`make run-dashboard` start the two interfaces; `docker compose up` starts everything.
No phase is considered "done" until its code imports cleanly and its tests pass.
