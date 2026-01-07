import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.models import CandidateEvidence

router = APIRouter()

@router.delete("/{uid}")
def delete_evidence(*, session: SessionDep, uid: str) -> Any:
    """
    Soft delete evidence.
    """
    evidence = session.get(CandidateEvidence, uid)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
        
    evidence.is_deleted = True
    session.add(evidence)
    session.commit()
    return {"message": "Evidence deleted successfully"}
