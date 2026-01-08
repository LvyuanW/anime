from typing import Any, cast

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import (
    ExtractionRun,
    ExtractionRunPublic,
    NormalizedScript,
    NormalizedScriptPublic,
    Script,
    ScriptDetailPublic,
)

router = APIRouter()

@router.get("/{uid}", response_model=ScriptDetailPublic)
def read_script(*, session: SessionDep, uid: str) -> Any:
    """
    Get script by ID (with content).
    """
    script = session.get(Script, uid)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.get("/{uid}/normalized", response_model=NormalizedScriptPublic)
def read_normalized_script(*, session: SessionDep, uid: str, version: str | None = None) -> Any:
    """
    Get normalized script.
    """
    script = session.get(Script, uid)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    query = select(NormalizedScript).where(NormalizedScript.script_uid == uid)
    if version:
        query = query.where(NormalizedScript.version == version)
    else:
        # Get latest
        query = query.order_by(cast(Any, NormalizedScript.created_at).desc())

    normalized = session.exec(query).first()
    if not normalized:
        raise HTTPException(status_code=404, detail="Normalized script not found")

    return normalized

@router.get("/{uid}/runs", response_model=list[ExtractionRunPublic])
def read_script_runs(*, session: SessionDep, uid: str) -> Any:
    """
    Get all extraction runs for a script.
    """
    script = session.get(Script, uid)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    statement = (
        select(ExtractionRun)
        .where(ExtractionRun.script_uid == uid)
        .order_by(cast(Any, ExtractionRun.created_at).desc())
    )
    runs = session.exec(statement).all()
    return runs
