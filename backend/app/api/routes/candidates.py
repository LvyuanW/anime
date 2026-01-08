from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.models import CandidateEntity, CandidateEntityPublic, CandidateEntityUpdate

router = APIRouter()

@router.patch("/{uid}", response_model=CandidateEntityPublic)
def update_candidate(*, session: SessionDep, uid: str, candidate_in: CandidateEntityUpdate) -> Any:
    """
    Update candidate entity (e.g. merge to canonical).
    """
    candidate = session.get(CandidateEntity, uid)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    update_data = candidate_in.model_dump(exclude_unset=True)
    candidate.sqlmodel_update(update_data)
    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    cand_public = CandidateEntityPublic.model_validate(candidate)
    return cand_public

@router.delete("/{uid}")
def delete_candidate(*, session: SessionDep, uid: str) -> Any:
    """
    Soft delete candidate entity.
    """
    candidate = session.get(CandidateEntity, uid)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.is_deleted = True
    session.add(candidate)
    session.commit()
    return {"message": "Candidate deleted successfully"}
