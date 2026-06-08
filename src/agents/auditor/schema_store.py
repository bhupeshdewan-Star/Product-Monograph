from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Optional

from .schemas import AuditSchema


def get_schema_store_dir() -> Path:
    custom = os.getenv("GLOBAL_AGENTS_SCHEMA_DIR")
    if custom:
        return Path(custom).expanduser().resolve()
    return Path(__file__).resolve().parent / "saved_schemas"


def ensure_schema_store_dir() -> Path:
    directory = get_schema_store_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def schema_path(schema_id: str) -> Path:
    return ensure_schema_store_dir() / f"{schema_id}.json"


def save_schema(schema: AuditSchema | dict) -> Path:
    if isinstance(schema, AuditSchema):
        payload = schema.model_dump(mode="json")
        schema_id = schema.schema_id
    else:
        payload = schema
        schema_id = schema["schema_id"]
    path = schema_path(schema_id)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_schema(schema_id: str) -> AuditSchema:
    path = schema_path(schema_id)
    if not path.exists():
        raise FileNotFoundError(f"Audit schema '{schema_id}' was not found at {path}")
    return AuditSchema.model_validate_json(path.read_text(encoding="utf-8"))


def list_schema_ids() -> list[str]:
    directory = ensure_schema_store_dir()
    return sorted(path.stem for path in directory.glob("*.json"))
