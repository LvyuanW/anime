import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.models import CanonicalAssetAlias

router = APIRouter()

@router.delete("/{uid}")
def delete_alias(*, session: SessionDep, uid: str) -> Any:
    """
    Remove alias.
    """
    alias = session.get(CanonicalAssetAlias, uid)
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")
        
    session.delete(alias)
    session.commit()
    return {"message": "Alias deleted successfully"}
