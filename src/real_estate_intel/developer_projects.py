from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    select,
)
from sqlalchemy.engine import Engine

from real_estate_intel.data_engine import create_postgres_engine, get_db_connection_string


DEVELOPER_PROJECTS_TABLE = "developer_projects"
metadata = MetaData()
developer_projects = Table(
    DEVELOPER_PROJECTS_TABLE,
    metadata,
    Column("id", String(36), primary_key=True),
    Column("workspace_hash", String(64), nullable=False, index=True),
    Column("project_name", String(160), nullable=False),
    Column("property_type", String(120), nullable=False, default=""),
    Column("assumptions_json", Text, nullable=False),
    Column("result_json", Text, nullable=False),
    Column("stress_json", Text, nullable=False),
    Column("score", Float, nullable=False, default=0),
    Column("margin_pct", Float, nullable=False, default=0),
    Column("profit", Float, nullable=False, default=0),
    Column("downside_profit", Float, nullable=False, default=0),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("workspace_hash", "project_name", name="uq_developer_workspace_project"),
)


def workspace_fingerprint(workspace_code: str) -> str:
    normalized = str(workspace_code or "").strip()
    if len(normalized) < 8:
        raise ValueError("Workspace code must contain at least 8 characters.")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def connect_developer_project_store(db_url: str | None = None) -> Engine | None:
    url = db_url or get_db_connection_string()
    if not url:
        return None
    engine = create_postgres_engine(url)
    initialize_developer_project_store(engine)
    return engine


def initialize_developer_project_store(engine: Engine) -> None:
    metadata.create_all(engine, tables=[developer_projects], checkfirst=True)


def save_developer_project(
    engine: Engine,
    *,
    workspace_code: str,
    project_name: str,
    property_type: str,
    assumptions: Any,
    result: dict[str, Any],
    stress: dict[str, Any],
) -> str:
    workspace_hash = workspace_fingerprint(workspace_code)
    name = str(project_name or "").strip()
    if not name:
        raise ValueError("Project name is required.")

    assumptions_payload = asdict(assumptions) if is_dataclass(assumptions) else dict(assumptions)
    now = datetime.now(timezone.utc)
    values = {
        "property_type": str(property_type or ""),
        "assumptions_json": _json_dump(assumptions_payload),
        "result_json": _json_dump(result),
        "stress_json": _json_dump(stress),
        "score": _number(result.get("development_score")),
        "margin_pct": _number(result.get("margin_pct")),
        "profit": _number(result.get("profit")),
        "downside_profit": _number(stress.get("downside_profit")),
        "updated_at": now,
    }
    with engine.begin() as connection:
        existing = connection.execute(
            select(developer_projects.c.id).where(
                developer_projects.c.workspace_hash == workspace_hash,
                developer_projects.c.project_name == name,
            )
        ).scalar_one_or_none()
        if existing:
            connection.execute(
                developer_projects.update()
                .where(developer_projects.c.id == existing)
                .values(**values)
            )
            return str(existing)

        project_id = str(uuid4())
        connection.execute(
            developer_projects.insert().values(
                id=project_id,
                workspace_hash=workspace_hash,
                project_name=name,
                created_at=now,
                **values,
            )
        )
        return project_id


def load_developer_projects(engine: Engine, *, workspace_code: str) -> list[dict[str, Any]]:
    workspace_hash = workspace_fingerprint(workspace_code)
    with engine.connect() as connection:
        rows = connection.execute(
            select(developer_projects)
            .where(developer_projects.c.workspace_hash == workspace_hash)
            .order_by(developer_projects.c.updated_at.desc())
        ).mappings()
        return [_restore_project(dict(row)) for row in rows]


def delete_developer_project(
    engine: Engine,
    *,
    workspace_code: str,
    project_name: str,
) -> bool:
    workspace_hash = workspace_fingerprint(workspace_code)
    with engine.begin() as connection:
        result = connection.execute(
            developer_projects.delete().where(
                developer_projects.c.workspace_hash == workspace_hash,
                developer_projects.c.project_name == str(project_name).strip(),
            )
        )
    return bool(result.rowcount)


def project_comparison_row(project: dict[str, Any]) -> dict[str, float | str]:
    result = dict(project.get("result", {}))
    stress = dict(project.get("stress", {}))
    assumptions = dict(project.get("assumptions", {}))
    return {
        "project": str(project.get("project_name", "مشروع بدون اسم")),
        "land_area_sqm": _number(assumptions.get("land_area_sqm")),
        "land_cost": _number(assumptions.get("land_cost")),
        "units": _number(result.get("units")),
        "sale_revenue": _number(result.get("sale_revenue")),
        "total_cost": _number(result.get("total_cost")),
        "profit": _number(result.get("profit")),
        "margin_pct": _number(result.get("margin_pct")),
        "roi_pct": _number(result.get("roi_pct")),
        "annualized_return_pct": _number(result.get("annualized_return_pct")),
        "development_score": _number(result.get("development_score")),
        "decision": str(result.get("decision", "")),
        "downside_profit": _number(stress.get("downside_profit")),
        "max_land_bid": _number(result.get("max_land_bid")),
    }


def _restore_project(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "project_name": str(row["project_name"]),
        "property_type": str(row.get("property_type", "")),
        "assumptions": _json_load(row.get("assumptions_json")),
        "result": _json_load(row.get("result_json")),
        "stress": _json_load(row.get("stress_json")),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _json_load(value: Any) -> dict[str, Any]:
    try:
        loaded = json.loads(str(value or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
