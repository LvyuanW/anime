import uuid
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import (
    CandidateEntity,
    CandidateEntityPublic,
    ExtractionRun,
    ExtractionRunCreate,
    ExtractionRunPublic,
)

router = APIRouter()

@router.post("/", response_model=ExtractionRunPublic)
def create_run(*, session: SessionDep, run_in: ExtractionRunCreate) -> Any:
    """
    Trigger a specific extraction step.
    """
    run = ExtractionRun.model_validate(
        run_in,
        update={
            "uid": f"run_{uuid.uuid4().hex}",
            "status": "running",
            "model_config_data": run_in.model_config_dict,
        },
    )
    # Clear model_config_dict if it was set via alias in init but we manually handled it
    # Actually model_validate will set what matches.
    # We mapped model_config_dict -> model_config_data manually?
    # run_in has model_config_dict. ExtractionRun has model_config_data.
    # The names don't match, so we need to pass it explicitly or rename in model.
    # I passed it in update.

    session.add(run)
    session.commit()
    session.refresh(run)
    return run

@router.get("/{uid}", response_model=ExtractionRunPublic)
def read_run(*, session: SessionDep, uid: str) -> Any:
    """
    Get run status.
    """
    run = session.get(ExtractionRun, uid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/{uid}/candidates", response_model=list[CandidateEntityPublic])
def read_run_candidates(*, session: SessionDep, uid: str, entity_type: str | None = None) -> Any:
    """
    Get candidates for a run.
    """
    run = session.get(ExtractionRun, uid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    query = (
        select(CandidateEntity)
        .where(CandidateEntity.run_uid == uid)
        .where(cast(Any, CandidateEntity.is_deleted).is_(False))
    )
    if entity_type:
        query = query.where(CandidateEntity.entity_type == entity_type)

    candidates = session.exec(query).all()

    return [CandidateEntityPublic.model_validate(c) for c in candidates]
