"""Controlled data ingestion for GEOMATRIX.

Uploaded datasets are treated as unverified by default. Only explicitly
approved REAL historical data can enter the training pool.
"""
import csv
import io
import json
import os
import uuid
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DataIngestionLog, HistoricalDelayRecord, Project
from ..schemas import IngestResult, IngestionLogOut

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

DATAGOVIN_BASE = "https://api.data.gov.in/resource"
DATAGOVIN_RESOURCES = {
    "land_acquisition": "9ef84268-d588-465a-a308-a864a43d0070",
    "infrastructure": "65f7ced4-ee4c-4b96-b9f0-d01038e49099",
}


def _normalise(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _field(row: dict[str, Any], *names: str) -> Any:
    normalised = {
        _normalise(key).lstrip("\ufeff").lower(): value
        for key, value in row.items()
        if key is not None
    }
    for name in names:
        value = normalised.get(name.lower())
        if value not in (None, ""):
            return value
    return None


def _float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = _normalise(value).lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _coordinates(lat: Any, lng: Any) -> tuple[float | None, float | None]:
    lat_value, lng_value = _float(lat), _float(lng)
    if lat_value is not None and not -90 <= lat_value <= 90:
        lat_value = None
    if lng_value is not None and not -180 <= lng_value <= 180:
        lng_value = None
    return lat_value, lng_value


def _admin_token_valid(token: str | None) -> bool:
    expected = os.getenv("ADMIN_API_TOKEN", "").strip()
    return bool(expected) and bool(token) and token == expected


def _requested_classification(row: dict[str, Any], admin_token: str | None, source_is_official: bool) -> str:
    if source_is_official:
        return "REAL"
    requested = _normalise(_field(row, "data_classification", "classification")).upper()
    if requested == "REAL" and _admin_token_valid(admin_token):
        return "REAL"
    return "USER_UPLOADED"


def _log_start(db: Session, source: str, source_url: str) -> DataIngestionLog:
    item = DataIngestionLog(
        id=str(uuid.uuid4()),
        source=source,
        source_name=source,
        source_url=source_url,
        started_at=datetime.utcnow(),
        triggered_at=datetime.utcnow(),
        status="running",
    )
    db.add(item)
    db.commit()
    return item


def _log_finish(db: Session, item: DataIngestionLog, fetched: int, saved: int, skipped: int, errors: list[str], status: str) -> None:
    item.finished_at = datetime.utcnow()
    item.records_fetched = fetched
    item.records_saved = saved
    item.records_skipped = skipped
    item.errors = errors[:20]
    item.error_message = errors[0] if errors else None
    item.status = status
    db.commit()


def _rows_from_upload(filename: str, content: bytes) -> list[dict[str, Any]]:
    if filename.lower().endswith(".json"):
        payload = json.loads(content.decode("utf-8-sig"))
        if isinstance(payload, list):
            return [r for r in payload if isinstance(r, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return [r for r in payload["records"] if isinstance(r, dict)]
        if isinstance(payload, dict):
            return [payload]
        raise ValueError("JSON must contain an object, list, or records array")

    decoded = content.decode("utf-8-sig")
    return [dict(row) for row in csv.DictReader(io.StringIO(decoded))]


@router.post("/datagovIn", response_model=IngestResult)
async def ingest_from_datagovin(
    source: str = Query("land_acquisition"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    resource_id = DATAGOVIN_RESOURCES.get(source)
    api_key = os.getenv("DATAGOVIN_API_KEY", "").strip()
    if not resource_id:
        raise HTTPException(400, "Unknown data.gov.in resource.")
    if not api_key:
        raise HTTPException(503, "DATAGOVIN_API_KEY is not configured.")

    url = f"{DATAGOVIN_BASE}/{resource_id}"
    params = {"api-key": api_key, "format": "json", "limit": str(limit)}
    log_item = _log_start(db, "datagovIn", url)
    errors: list[str] = []
    records_raw: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            records_raw = payload.get("records", []) if isinstance(payload, dict) else []
    except Exception as exc:
        errors.append(f"data.gov.in request failed: {type(exc).__name__}")
        _log_finish(db, log_item, 0, 0, 0, errors, "failed")
        return IngestResult(source="datagovIn", records_fetched=0, records_saved=0, records_skipped=0, errors=errors, status="failed")

    saved = skipped = 0
    for record in records_raw:
        try:
            source_record_id = _normalise(record.get("id") or record.get("_id") or record.get("project_id"))
            if not source_record_id:
                errors.append("Skipped official record without a stable identifier")
                skipped += 1
                continue
            if db.query(Project).filter_by(source_record_id=source_record_id).first():
                skipped += 1
                continue

            lat, lng = _coordinates(record.get("latitude") or record.get("lat"), record.get("longitude") or record.get("lng") or record.get("lon"))
            project = Project(
                id=str(uuid.uuid4()),
                project_code=f"DGI-{source_record_id[:20]}",
                name=_normalise(record.get("project_name") or record.get("name") or "Unnamed project")[:200],
                state=_normalise(record.get("state") or record.get("state_name"))[:100] or "Unknown",
                district=_normalise(record.get("district") or record.get("district_name"))[:100] or "Unknown",
                authority=_normalise(record.get("authority") or record.get("agency") or record.get("implementing_agency"))[:200] or "Unknown",
                project_type=_normalise(record.get("project_type") or record.get("type") or "Infrastructure")[:100],
                latitude=lat,
                longitude=lng,
                current_stage=_normalise(record.get("stage") or record.get("current_stage"))[:100] or None,
                status=_normalise(record.get("status"))[:50] or None,
                land_required=_float(record.get("land_required") or record.get("land_area"), 0.0) or 0.0,
                land_acquired=_float(record.get("land_acquired"), 0.0) or 0.0,
                affected_families=_int(record.get("affected_families") or record.get("families"), 0) or 0,
                source_name="data.gov.in",
                source_url=f"{url}?resource_id={resource_id}",
                source_record_id=source_record_id,
                validation_status="validated",
                data_classification="REAL",
            )
            db.add(project)
            saved += 1
        except Exception:
            errors.append("Failed to parse an official project record")
            skipped += 1

    db.commit()
    status = "success" if not errors else "partial"
    _log_finish(db, log_item, len(records_raw), saved, skipped, errors, status)
    return IngestResult(source="datagovIn", records_fetched=len(records_raw), records_saved=saved, records_skipped=skipped, errors=errors, status=status)


@router.post("/upload", response_model=IngestResult)
async def upload_data(
    file: UploadFile = File(...),
    data_type: str = Query("projects", pattern="^(projects|historical)$"),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
):
    filename = (file.filename or "").strip()
    if not filename.lower().endswith((".csv", ".json")):
        raise HTTPException(400, "Only CSV and JSON files are accepted.")

    content = await file.read()
    source_url = _normalise(_field({}, "source_url")) or f"file_upload:{filename}"
    log_item = _log_start(db, f"csv_{data_type}", source_url)
    errors: list[str] = []

    try:
        rows = _rows_from_upload(filename, content)
    except Exception as exc:
        errors.append(f"File parse error: {type(exc).__name__}")
        _log_finish(db, log_item, 0, 0, 0, errors, "failed")
        return IngestResult(source=f"csv_{data_type}", records_fetched=0, records_saved=0, records_skipped=0, errors=errors, status="failed")

    saved = skipped = 0
    official_import = _admin_token_valid(x_admin_token)

    for index, row in enumerate(rows, start=2):
        try:
            if data_type == "historical":
                project_code = _normalise(_field(row, "project_code", "project_id", "source_record_id", "id"))
                state = _normalise(_field(row, "state", "state_or_region", "state_name"))
                project_type = _normalise(_field(row, "project_type", "sector"))
                delayed_value = _field(row, "delayed", "delay_flag", "land_acquisition_delay_flag")
                if not project_code or not state or not project_type:
                    raise ValueError(f"row {index}: project_code, state and project_type are required")

                delayed = _bool(delayed_value)
                if delayed is None:
                    months = _float(_field(row, "delay_months_original"))
                    if months is not None:
                        delayed = months > 0
                if delayed is None:
                    raise ValueError(f"row {index}: explicit delayed/delay_flag label required")

                record_id = _normalise(_field(row, "source_record_id", "id", "project_code", "project_id"))
                if not record_id:
                    raise ValueError(f"row {index}: stable source_record_id required")
                if db.query(HistoricalDelayRecord).filter_by(source_record_id=record_id).first():
                    skipped += 1
                    continue

                rec = HistoricalDelayRecord(
                    id=str(uuid.uuid4()),
                    project_code=project_code[:50],
                    state=state[:100],
                    project_type=project_type[:100],
                    land_area_ha=_float(_field(row, "land_area_ha", "land_required_ha", "land_required")),
                    affected_families=_int(_field(row, "affected_families", "families_affected", "families")),
                    pending_claims=_int(_field(row, "pending_claims", "objection_count", "claims_pending")),
                    legal_cases=_int(_field(row, "legal_cases", "case_count", "court_cases")),
                    doc_completeness_pct=_float(_field(row, "doc_completeness_pct", "document_completeness_pct", "physical_progress_pct")),
                    approval_pending=_bool(_field(row, "approval_pending", "approval_pending_flag")),
                    rr_pending=_int(_field(row, "rr_pending", "rr_pending_count")),
                    overdue_milestones=_int(_field(row, "overdue_milestones", "overdue_milestone_count")),
                    # Do not invent days from months. Keep regression target null
                    # unless actual_delay_days is explicitly supplied.
                    actual_delay_days=_int(_field(row, "actual_delay_days")),
                    delayed=delayed,
                    validation_status="validated" if official_import else "pending_review",
                    data_classification="REAL" if official_import else "USER_UPLOADED",
                    source_name=filename,
                    source_url=_normalise(_field(row, "source_url")) or source_url,
                    source_record_id=record_id,
                )
                db.add(rec)
                saved += 1
            else:
                project_code = _normalise(_field(row, "project_code", "project_id", "source_record_id", "id"))
                name = _normalise(_field(row, "name", "project_name", "canonical_project_name", "source_project_name"))
                state = _normalise(_field(row, "state", "state_or_region", "state_name"))
                project_type = _normalise(_field(row, "project_type", "sector"))
                authority = _normalise(_field(row, "authority", "implementing_agency", "agency"))
                if not project_code or not name or not state or not project_type:
                    raise ValueError(f"row {index}: project_code, name, state and project_type are required")
                record_id = _normalise(_field(row, "source_record_id", "id", "project_id", "project_code"))
                if not record_id:
                    raise ValueError(f"row {index}: stable source_record_id required")
                if db.query(Project).filter_by(source_record_id=record_id).first():
                    skipped += 1
                    continue

                lat, lng = _coordinates(_field(row, "latitude", "lat"), _field(row, "longitude", "lon", "lng"))
                project = Project(
                    id=str(uuid.uuid4()),
                    project_code=project_code[:50],
                    name=name[:200],
                    state=state[:100],
                    district=_normalise(_field(row, "district", "district_name"))[:100] or "Unknown",
                    authority=authority[:200] or "Unknown",
                    project_type=project_type[:100],
                    latitude=lat,
                    longitude=lng,
                    current_stage=_normalise(_field(row, "current_stage", "stage", "current_acquisition_stage"))[:100] or None,
                    status=_normalise(_field(row, "status", "project_status"))[:50] or None,
                    land_required=_float(_field(row, "land_required", "land_required_ha", "land_area_ha")),
                    land_acquired=_float(_field(row, "land_acquired", "land_acquired_ha")),
                    affected_families=_int(_field(row, "affected_families", "families_affected")),
                    compensation_status=_normalise(_field(row, "compensation_status", "compensation_issue"))[:50] or None,
                    objection_count=_int(_field(row, "objection_count", "public_objection_issue")),
                    legal_case_count=_int(_field(row, "legal_case_count", "legal_issue")),
                    rr_status=_normalise(_field(row, "rr_status"))[:50] or None,
                    env_clearance_status=_normalise(_field(row, "env_clearance_status", "environment_clearance_status"))[:50] or None,
                    forest_clearance_status=_normalise(_field(row, "forest_clearance_status", "forest_clearance_issue"))[:50] or None,
                    crz_status=_normalise(_field(row, "crz_status"))[:50] or None,
                    doc_completeness_pct=_float(_field(row, "doc_completeness_pct", "document_completeness_pct")),
                    approval_pending=_bool(_field(row, "approval_pending", "approval_issue")),
                    overdue_milestones=_int(_field(row, "overdue_milestones", "overdue_milestone_count")),
                    validation_status="validated" if official_import else "pending_review",
                    data_classification="REAL" if official_import else "USER_UPLOADED",
                    source_name=filename,
                    source_url=_normalise(_field(row, "source_url")) or source_url,
                    source_record_id=record_id,
                )
                db.add(project)
                saved += 1
        except Exception as exc:
            errors.append(str(exc)[:240])
            skipped += 1

    db.commit()
    status = "success" if not errors else "partial"
    _log_finish(db, log_item, len(rows), saved, skipped, errors, status)
    return IngestResult(source=f"csv_{data_type}", records_fetched=len(rows), records_saved=saved, records_skipped=skipped, errors=errors, status=status)


@router.get("/log", response_model=list[IngestionLogOut])
def get_ingestion_log(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return (
        db.query(DataIngestionLog)
        .order_by(DataIngestionLog.started_at.desc())
        .limit(limit)
        .all()
    )
