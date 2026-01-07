import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import CandidateEntity, CandidateEntityUpdate, CandidateEntityPublic, CandidateEvidence, CandidateEvidenceCreate, CandidateEvidencePublic

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
    
    # We need to return evidences too to match Public model
    # Usually update doesn't change evidences, so we can fetch them or return empty if we don't care about showing them in update response.
    # But response_model expects them.
    evidences = session.exec(select(CandidateEvidence).where(CandidateEvidence.candidate_uid == uid).where(CandidateEvidence.is_deleted == False)).all()
    
    cand_public = CandidateEntityPublic.model_validate(candidate)
    cand_public.evidences = [CandidateEvidencePublic.model_validate(ev) for ev in evidences]
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

@router.post("/{uid}/evidences", response_model=CandidateEvidencePublic)
def create_evidence(*, session: SessionDep, uid: str, evidence_in: CandidateEvidenceCreate) -> Any:
    """
    Add evidence to a candidate.
    """
    candidate = session.get(CandidateEntity, uid)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    evidence = CandidateEvidence.model_validate(
        evidence_in,
        update={
            "uid": f"evid_{uuid.uuid4().hex}",
            "candidate_uid": uid
        }
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)
    return evidence
