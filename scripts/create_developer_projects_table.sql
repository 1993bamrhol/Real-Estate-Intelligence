create table if not exists public.developer_projects (
    id varchar(36) primary key,
    workspace_hash varchar(64) not null,
    project_name varchar(160) not null,
    property_type varchar(120) not null default '',
    assumptions_json text not null,
    result_json text not null,
    stress_json text not null,
    score double precision not null default 0,
    margin_pct double precision not null default 0,
    profit double precision not null default 0,
    downside_profit double precision not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_developer_workspace_project unique (workspace_hash, project_name)
);

create index if not exists idx_developer_projects_workspace
    on public.developer_projects(workspace_hash, updated_at desc);

comment on table public.developer_projects is
    'Qareena developer feasibility projects. Workspace codes are stored only as SHA-256 fingerprints.';
