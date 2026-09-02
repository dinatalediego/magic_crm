create schema if not exists decision_intelligence;
create schema if not exists features;

create table if not exists decision_intelligence.pricing_model_registry (
    model_id bigserial primary key,
    model_name text not null,
    model_family text not null,
    version text not null,
    target text not null,
    unit_of_analysis text not null,
    training_window tstzrange,
    features_version text,
    dataset_version text,
    metric_primary text,
    metric_value numeric,
    status text not null check (status in ('research','challenger','champion','retired')),
    valid_from timestamptz,
    valid_to timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    approved_at timestamptz,
    approved_by text,
    unique (model_name, version)
);

create table if not exists decision_intelligence.pricing_recommendation (
    recommendation_id uuid primary key,
    created_at timestamptz not null,
    project text not null,
    unit_code text not null,
    typology text not null,
    current_price numeric(18,2) not null,
    model_price numeric(18,2) not null,
    recommended_price numeric(18,2) not null,
    increase_pct numeric(12,8) not null,
    absorption_score numeric(8,4),
    confidence numeric(8,6),
    model_name text not null,
    model_version text not null,
    reason_codes jsonb not null default '[]'::jsonb,
    constraints_applied jsonb not null default '[]'::jsonb,
    decision_status text not null check (decision_status in ('proposed','approved','rejected','executed','observed')),
    approved_by text,
    approved_at timestamptz,
    executed_in_crm boolean not null default false,
    executed_at timestamptz,
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists ix_pricing_recommendation_unit_created
    on decision_intelligence.pricing_recommendation (unit_code, created_at desc);

create table if not exists decision_intelligence.pricing_outcome (
    outcome_id bigserial primary key,
    recommendation_id uuid not null references decision_intelligence.pricing_recommendation(recommendation_id),
    observed_at timestamptz not null default now(),
    actual_sale_price numeric(18,2),
    actual_sale_date date,
    actual_days_to_sale integer,
    separation_created boolean,
    sale_completed boolean,
    cancelled boolean,
    outcome_metadata jsonb not null default '{}'::jsonb
);

create table if not exists decision_intelligence.crm_event_log (
    crm_event_id bigserial primary key,
    provider text not null default 'sperant',
    external_event_id text,
    event_type text not null,
    occurred_at timestamptz,
    received_at timestamptz not null default now(),
    payload jsonb not null,
    processing_status text not null default 'received',
    error_message text,
    unique (provider, external_event_id)
);

create table if not exists features.pricing_unit_snapshot (
    snapshot_at timestamptz not null,
    project text not null,
    unit_code text not null,
    typology text not null,
    current_price numeric(18,2) not null,
    days_in_stock integer not null,
    stock_units_typology integer not null,
    sales_30d_typology integer not null,
    separations_30d_typology integer not null,
    benchmark_price numeric(18,2),
    target_gap_pct numeric(12,8),
    source_lineage jsonb not null default '{}'::jsonb,
    primary key (snapshot_at, unit_code)
);
