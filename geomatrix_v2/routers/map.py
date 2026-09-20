"""GIS map endpoints backed by stored project coordinates."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project
from ..schemas import GeoFeature, GeoFeatureCollection

router = APIRouter(prefix="/api/map", tags=["map"])

STATE_COORDINATES = {
    "andhra pradesh": (15.9129, 79.7400),
    "telangana": (18.1124, 79.0193),
    "odisha": (20.9517, 85.0985),
    "bihar": (25.0961, 85.3131),
    "punjab": (31.1471, 75.3412),
    "delhi": (28.7041, 77.1025),
    "gujarat": (22.2587, 71.1924),
    "karnataka": (15.3173, 75.7139),
    "west bengal": (22.9868, 87.8550),
    "maharashtra": (19.7515, 75.7139),
    "chhattisgarh": (21.2787, 81.8661),
    "uttarakhand": (30.0668, 79.0193),
}
DEFAULT_COORDS = (20.5937, 78.9629)


@router.get("/geojson", response_model=GeoFeatureCollection)
def get_geojson(
    risk_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Project)
    if risk_level:
        q = q.filter(Project.risk_level == risk_level)
    projects = q.order_by(Project.updated_at.desc()).all()

    features = []
    for idx, project in enumerate(projects):
        lat, lng = project.latitude, project.longitude
        # Only use deterministic state centroid when coordinates are genuinely absent.
        if lat is None or lng is None:
            base_lat, base_lng = STATE_COORDINATES.get(
                (project.state or "").strip().lower(), DEFAULT_COORDS
            )
            lat = base_lat + ((idx % 5) - 2) * 0.15
            lng = base_lng + ((idx // 5) % 5 - 2) * 0.15

        features.append(
            GeoFeature(
                geometry={"type": "Point", "coordinates": [lng, lat]},
                properties={
                    "id": project.id,
                    "project_code": project.project_code,
                    "name": project.name,
                    "state": project.state,
                    "district": project.district,
                    "authority": project.authority,
                    "project_type": project.project_type,
                    "current_stage": project.current_stage,
                    "status": project.status,
                    "risk_score": project.risk_score,
                    "risk_level": project.risk_level,
                    "delay_probability": project.delay_probability,
                    "predicted_delay_days": project.predicted_delay_days,
                    "land_required": project.land_required,
                    "affected_families": project.affected_families,
                    "data_classification": project.data_classification,
                    "source_url": project.source_url,
                },
            )
        )
    return GeoFeatureCollection(features=features)


@router.get("/summary")
def map_summary(db: Session = Depends(get_db)):
    total = db.query(Project).count()
    with_coords = (
        db.query(Project)
        .filter(Project.latitude.isnot(None), Project.longitude.isnot(None))
        .count()
    )
    return {
        "total_projects": total,
        "projects_with_coordinates": with_coords,
        "projects_without_coordinates": total - with_coords,
    }
