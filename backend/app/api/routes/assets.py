import uuid
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import (
    CanonicalAsset,
    CanonicalAssetAlias,
    CanonicalAssetAliasCreate,
    CanonicalAssetAliasPublic,
    CanonicalAssetCreate,
    CanonicalAssetPublic,
    CanonicalAssetUpdate,
)

router = APIRouter()

@router.post("/", response_model=CanonicalAssetPublic)
def create_asset(*, session: SessionDep, asset_in: CanonicalAssetCreate) -> Any:
    """
    Create a new canonical asset manually.
    """
    asset = CanonicalAsset(
        uid=f"asset_{uuid.uuid4().hex}",
        project_uid=asset_in.project_uid,
        name=asset_in.name,
        type=asset_in.type,
        description=asset_in.description,
        status="active",
    )
    session.add(asset)
    session.commit()

    # Create aliases
    created_aliases = []
    for alias_str in asset_in.aliases:
        alias_obj = CanonicalAssetAlias(
            uid=f"alias_{uuid.uuid4().hex}",
            asset_uid=asset.uid,
            alias=alias_str,
        )
        session.add(alias_obj)
        created_aliases.append(alias_obj)

    session.commit()
    session.refresh(asset)

    asset_public = CanonicalAssetPublic.model_validate(asset)
    asset_public.aliases = [CanonicalAssetAliasPublic.model_validate(a) for a in created_aliases]
    return asset_public

@router.get("/", response_model=list[CanonicalAssetPublic])
def read_assets(
    session: SessionDep,
    project_uid: str | None = None,
    type: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List canonical assets.
    """
    query = select(CanonicalAsset)
    if project_uid:
        query = query.where(CanonicalAsset.project_uid == project_uid)
    if type:
        query = query.where(CanonicalAsset.type == type)

    query = query.offset(skip).limit(limit)
    assets = session.exec(query).all()

    # Bulk fetch aliases
    if not assets:
        return []

    asset_uids = [a.uid for a in assets]
    alias_query = select(CanonicalAssetAlias).where(
        cast(Any, CanonicalAssetAlias.asset_uid).in_(asset_uids)
    )
    aliases = session.exec(alias_query).all()

    alias_map: dict[str, list[CanonicalAssetAlias]] = {uid: [] for uid in asset_uids}
    for a in aliases:
        alias_map[a.asset_uid].append(a)

    result = []
    for asset in assets:
        public = CanonicalAssetPublic.model_validate(asset)
        public.aliases = [CanonicalAssetAliasPublic.model_validate(a) for a in alias_map[asset.uid]]
        result.append(public)

    return result

@router.get("/{uid}", response_model=CanonicalAssetPublic)
def read_asset(*, session: SessionDep, uid: str) -> Any:
    """
    Get asset detail.
    """
    asset = session.get(CanonicalAsset, uid)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    aliases = session.exec(select(CanonicalAssetAlias).where(CanonicalAssetAlias.asset_uid == uid)).all()

    public = CanonicalAssetPublic.model_validate(asset)
    public.aliases = [CanonicalAssetAliasPublic.model_validate(a) for a in aliases]
    return public

@router.patch("/{uid}", response_model=CanonicalAssetPublic)
def update_asset(*, session: SessionDep, uid: str, asset_in: CanonicalAssetUpdate) -> Any:
    """
    Update asset.
    """
    asset = session.get(CanonicalAsset, uid)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = asset_in.model_dump(exclude_unset=True)
    asset.sqlmodel_update(update_data)
    session.add(asset)
    session.commit()
    session.refresh(asset)

    aliases = session.exec(select(CanonicalAssetAlias).where(CanonicalAssetAlias.asset_uid == uid)).all()

    public = CanonicalAssetPublic.model_validate(asset)
    public.aliases = [CanonicalAssetAliasPublic.model_validate(a) for a in aliases]
    return public

@router.post("/{uid}/aliases", response_model=CanonicalAssetAliasPublic)
def create_asset_alias(*, session: SessionDep, uid: str, alias_in: CanonicalAssetAliasCreate) -> Any:
    """
    Add alias to asset.
    """
    asset = session.get(CanonicalAsset, uid)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    alias_obj = CanonicalAssetAlias(
        uid=f"alias_{uuid.uuid4().hex}",
        asset_uid=uid,
        alias=alias_in.alias,
    )
    session.add(alias_obj)
    session.commit()
    session.refresh(alias_obj)
    return alias_obj
