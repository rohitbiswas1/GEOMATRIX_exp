"""Portfolio analytics derived only from persisted database/model outputs."""
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, Project, RiskPrediction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    scored = [p for p in projects if p.risk_score is not None]
    probabilities = [p.delay_probability for p in projects if p.delay_probability is not None]
    return {
        "totalProjects": len(projects),
        "critical": sum(p.risk_level == "Critical" for p in projects),
        "high": sum(p.risk_level == "High" for p in projects),
        "medium": sum(p.risk_level == "Medium" for p in projects),
        "low": sum(p.risk_level == "Low" for p in projects),
        "scoredProjects": len(scored),
        "avgRiskScore": round(sum(p.risk_score for p in scored) / len(scored), 2) if scored else None,
        "avgDelayProbability": round(sum(probabilities) / len(probabilities), 4) if probabilities else None,
        "totalLandHa": round(sum(p.land_required or 0 for p in projects), 2),
        "totalFamilies": sum(p.affected_families or 0 for p in projects),
        "alertsOpen": db.query(Alert).filter(Alert.status == "Open").count(),
    }


@router.get("/drivers")
def drivers(db: Session = Depends(get_db)):
    buckets: dict[str, list[float]] = defaultdict(list)
    for prediction in db.query(RiskPrediction).all():
        values = prediction.shap_values or {}
        if not isinstance(values, dict):
            continue
        for feature, value in values.items():
            try:
                buckets[str(feature)].append(abs(float(value)))
            except (TypeError, ValueError):
                continue
    items = [
        {
            "feature": feature,
            "mean_abs_shap": round(sum(values) / len(values), 6),
            "sample_count": len(values),
        }
        for feature, values in buckets.items()
        if values
    ]
    items.sort(key=lambda item: item["mean_abs_shap"], reverse=True)
    return items


@router.get("/stages")
def stages(db: Session = Depends(get_db)):
    buckets: dict[str, list[float]] = defaultdict(list)
    for project in db.query(Project).all():
        stage = (project.current_stage or "Unknown").strip() or "Unknown"
        if project.risk_score is not None:
            buckets[stage].append(project.risk_score)
        else:
            buckets.setdefault(stage, [])
    return [
        {
            "stage": stage,
            "projects": len(values) if values else sum(
                1 for p in db.query(Project).all()
                if ((p.current_stage or "Unknown").strip() or "Unknown") == stage
            ),
            "avgRiskScore": round(sum(values) / len(values), 2) if values else None,
        }
        for stage, values in sorted(buckets.items())
    ]
