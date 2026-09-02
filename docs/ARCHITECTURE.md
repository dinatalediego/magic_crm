# MAGIC CRM Architecture — Foundation v0.1

## Purpose

MAGIC CRM is a Commercial Decision Intelligence system. Pricing is its first governed decision domain.

The system must preserve the complete loop:

`data -> evidence -> recommendation -> policy -> human decision -> CRM execution -> observed outcome -> learning`

## Architectural principles

1. SQL and deterministic rules before ML when they can answer the question.
2. Models propose; policies constrain; humans retain approval authority in v0.1.
3. Every recommendation must be reproducible from versioned features and model metadata.
4. CRM integration is an adapter, never a dependency of the pricing core.
5. Webhook events are persisted before processing so no commercial event is silently lost.
6. Outcomes are first-class records, not dashboard annotations.
7. Champion/challenger promotion requires measured evidence.

## Components

### Warehouse and feature layer

The warehouse remains the source of analytical truth. `features.pricing_unit_snapshot` is the minimum contract consumed by the pricing engine. It intentionally stores source lineage.

### Absorption Engine

The first model is transparent and deterministic. It combines sales velocity, separation velocity, stock scarcity and inventory aging into a 0-100 score.

It is a baseline, not a claim of causal optimality.

### Pricing Engine

The pricing engine converts the absorption signal and project target pressure into a price opportunity. It then applies explicit constraints such as maximum increase, market benchmark and commercial price floors/ceilings.

### Model Registry

`decision_intelligence.pricing_model_registry` records model family, version, analytical unit, dataset/features versions, metrics and lifecycle status.

### Decision Memory

`decision_intelligence.pricing_recommendation` records what MAGIC proposed and why. Approval and CRM execution are separate states.

### Outcome Memory

`decision_intelligence.pricing_outcome` records what actually happened after a recommendation. This is the future training/evaluation substrate.

### Sperant adapter

`SperantGateway` is a protocol. The real API adapter is replaceable and endpoint paths are configurable. Credentials are never committed.

Webhook events are mapped to three initial actions:

- sale/separation/unit event -> recompute pricing
- lead/proforma event -> refresh demand features
- unknown event -> persist only

## Next model families

The registry is designed to admit, without redesigning the system:

- elasticity models
- survival / time-to-sale
- willingness-to-pay
- demand forecasting
- uplift / treatment-effect models
- inventory optimization
- portfolio revenue optimization

These should enter as challengers against the deterministic baseline.
