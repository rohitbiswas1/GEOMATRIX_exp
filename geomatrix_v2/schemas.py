"""Strict API schemas for GEOMATRIX."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_code: str
    name: str
    state: str
    district: str
    authority: str
    project_type: str
    description: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    land_required: float = Field(ge=0)
    land_acquired: float = Field(ge=0)
    affected_families: int = Field(ge=0)
    current_stage: Optional[str] = None
    status: Optional[str] = None
    compensation_status: Optional[str] = None
    objection_count: Optional[int] = Field(default=None, ge=0)
    legal_case_count: Optional[int] = Field(default=None, ge=0)
    rr_status: Optional[str] = None
    env_clearance_status: Optional[str] = None
    forest_clearance_status: Optional[str] = None
    crz_status: Optional[str] = None
    doc_completeness_pct: Optional[float] = Field(default=None, ge=0, le=100)
    approval_pending: Optional[bool] = None
    overdue_milestones: Optional[int] = Field(default=None, ge=0)
    risk_score: Optional[float] = Field(default=None, ge=0, le=100)
    risk_level: Optional[str] = None
    delay_probability: Optional[float] = Field(default=None, ge=0, le=1)
    predicted_delay_days: Optional[int] = Field(default=None, ge=0)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    primary_driver: Optional[str] = None
    source_url: Optional[str] = None
    source_record_id: Optional[str] = None
    source_name: Optional[str] = None
    validation_status: Optional[str] = None
    data_classification: Optional[str] = None
    imported_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProjectCreate(BaseModel):
    project_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    state: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)
    authority: str = Field(min_length=1, max_length=200)
    project_type: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    land_required: Optional[float] = Field(default=None, ge=0)
    land_acquired: Optional[float] = Field(default=None, ge=0)
    affected_families: Optional[int] = Field(default=None, ge=0)
    current_stage: Optional[str] = None
    status: Optional[str] = None
    compensation_status: Optional[str] = None
    objection_count: Optional[int] = Field(default=None, ge=0)
    legal_case_count: Optional[int] = Field(default=None, ge=0)
    rr_status: Optional[str] = None
    env_clearance_status: Optional[str] = None
    forest_clearance_status: Optional[str] = None
    crz_status: Optional[str] = None
    doc_completeness_pct: Optional[float] = Field(default=None, ge=0, le=100)
    approval_pending: Optional[bool] = None
    overdue_milestones: Optional[int] = Field(default=None, ge=0)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    state: Optional[str] = Field(default=None, min_length=1, max_length=100)
    district: Optional[str] = Field(default=None, min_length=1, max_length=100)
    authority: Optional[str] = Field(default=None, min_length=1, max_length=200)
    project_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    land_required: Optional[float] = Field(default=None, ge=0)
    land_acquired: Optional[float] = Field(default=None, ge=0)
    affected_families: Optional[int] = Field(default=None, ge=0)
    current_stage: Optional[str] = None
    status: Optional[str] = None
    compensation_status: Optional[str] = None
    objection_count: Optional[int] = Field(default=None, ge=0)
    legal_case_count: Optional[int] = Field(default=None, ge=0)
    rr_status: Optional[str] = None
    env_clearance_status: Optional[str] = None
    forest_clearance_status: Optional[str] = None
    crz_status: Optional[str] = None
    doc_completeness_pct: Optional[float] = Field(default=None, ge=0, le=100)
    approval_pending: Optional[bool] = None
    overdue_milestones: Optional[int] = Field(default=None, ge=0)

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    project_name: Optional[str] = None
    severity: str
    reason: str
    detected_at: datetime
    recommended_action: Optional[str] = None
    status: str

class ShapFeature(BaseModel):
    feature: str
    shap_value: float
    direction: str
    description: str
    display_name: Optional[str] = None
    feature_value: Optional[float] = None

class ModelStatusOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    trained: bool
    algorithm: Optional[str] = None
    trained_at: Optional[str] = None
    n_samples: Optional[int] = None
    precision: Optional[float] = Field(default=None, ge=0, le=1)
    recall: Optional[float] = Field(default=None, ge=0, le=1)
    f1_score: Optional[float] = Field(default=None, ge=0, le=1)
    roc_auc: Optional[float] = Field(default=None, ge=0, le=1)
    rmse: Optional[float] = Field(default=None, ge=0)
    accuracy: Optional[float] = Field(default=None, ge=0, le=1)
    feature_names: Optional[List[str]] = None
    model_version: Optional[str] = None
    n_unique_classes: Optional[int] = None
    class_counts: Optional[Dict[str, int]] = None
    message: str

class IngestResult(BaseModel):
    source: str
    records_fetched: int
    records_saved: int
    records_skipped: int
    errors: List[str]
    status: str

class IngestionLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source: str
    source_url: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    records_fetched: int
    records_saved: int
    records_skipped: int
    errors: Optional[Any] = None
    status: str

class GeoFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class GeoFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoFeature]

class DashboardSummary(BaseModel):
    total_projects: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_land_ha: float
    total_families: int
    avg_risk_score: Optional[float]
    alerts_open: int
    data_available: bool
    message: str

class ProjectValidation(BaseModel):
    project_id: str
    missing_fields: List[str]
    can_predict: bool
    message: str

class ProjectActionCreate(BaseModel):
    action_type: str = Field(min_length=2, max_length=50)
    assigned_to: str = Field(min_length=1, max_length=200)
    priority: str = Field(default="Medium", pattern="^(Critical|High|Medium|Low)$")
    due_date: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=4000)

class ProjectActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    action_type: str
    assigned_to: str
    priority: str
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
