# MAGIC CRM

Commercial Decision Intelligence foundation for pricing analytics, CRM execution, and observed-outcome learning.

## Foundation v0.1

MAGIC connects a data warehouse to a governed pricing decision loop:

`warehouse -> features -> model -> policy -> recommendation -> decision -> CRM -> outcome -> learning`

The first vertical slice intentionally uses a transparent absorption/rules baseline before ML. It can later be challenged by elasticity, survival, willingness-to-pay, uplift, demand or optimization models without changing the decision-memory contract.

## What is included

- Python 3.11 package under `src/magic`
- deterministic Absorption Engine
- constrained Pricing Engine
- minimal Streamlit Pricing Console for daily use
- local approve/reject Decision Memory for the console
- typed domain contracts with Pydantic
- replaceable Sperant API gateway interface
- webhook event classification
- PostgreSQL schemas for Model Registry, Decision Memory, Outcome Memory, CRM Event Log and pricing feature snapshots
- pytest tests and GitHub Actions CI
- VS Code defaults and debug launchers
- architecture documentation

## Quick start from VS Code / PowerShell

```powershell
git clone https://github.com/dinatalediego/magic_crm.git
cd magic_crm
git checkout feat/pricing-model-master
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[all]"
pytest -q
python -m magic.cli
```

### Daily Pricing Console

Run:

```powershell
streamlit run apps/pricing_console.py
```

Or press `F5` in VS Code and select **MAGIC Pricing Console**.

The minimum daily flow is:

`unit signals -> recommendation -> explanation -> guardrails -> approve/reject -> decision log`

The console currently lets an analyst enter one unit snapshot, review the recommended price, absorption score, confidence, reason codes and applied constraints, then approve or reject the recommendation. Decisions are written locally to `data/local/pricing_decisions.jsonl`, which is ignored by Git. This local log is deliberately temporary: the production target remains `decision_intelligence.pricing_recommendation` in PostgreSQL.

No button in the console changes Sperant prices in v0.1.

## Database foundation

Apply `sql/001_foundation.sql` to the target PostgreSQL database. The script only creates schemas, tables and indexes with `if not exists`; it does not drop or truncate existing objects.

Core tables:

- `decision_intelligence.pricing_model_registry`
- `decision_intelligence.pricing_recommendation`
- `decision_intelligence.pricing_outcome`
- `decision_intelligence.crm_event_log`
- `features.pricing_unit_snapshot`

## Sperant integration

The pricing core depends on the `SperantGateway` protocol, not on a concrete endpoint contract. `HttpSperantGateway` is the initial adapter and keeps base URL, token and endpoint paths configurable.

Copy `.env.example` to `.env` locally and never commit real credentials.

Before activating writes to Sperant, confirm the real API endpoint contract and use human approval for price-changing actions. Webhook payloads should be persisted in `crm_event_log` before downstream processing.

## Baseline model

The v0.1 absorption score combines:

- 30-day sales velocity
- 30-day separation velocity
- typology stock scarcity
- inventory aging

The Pricing Engine then incorporates project target pressure and enforces explicit constraints such as maximum allowed increase, market benchmark, commercial floor and commercial ceiling.

This model is deliberately interpretable. It is the benchmark that future statistical and ML challengers must beat with observed outcomes.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Safety boundary

Foundation v0.1 produces recommendations and records human decisions. It does not autonomously mutate CRM prices. CRM execution remains an explicit, logged step until the organization has sufficient validation, rollback and monitoring controls.
