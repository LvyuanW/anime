import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import EmailStr
from sqlalchemy import Column, DateTime, Index, JSON, func
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

# Entity Extraction Models

class Project(SQLModel, table=True):
    uid: str = Field(primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))

class ProjectCreate(SQLModel):
    name: str
    description: str | None = None

class ProjectPublic(SQLModel):
    uid: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

class Script(SQLModel, table=True):
    uid: str = Field(primary_key=True)
    project_uid: str = Field(index=True)
    name: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))

class ScriptCreate(SQLModel):
    name: str
    content: str

class ScriptListPublic(SQLModel):
    uid: str
    name: str
    created_at: datetime

class ScriptDetailPublic(ScriptListPublic):
    content: str
    project_uid: str

class NormalizedScript(SQLModel, table=True):
    __tablename__ = "normalized_script"
    uid: str = Field(primary_key=True)
    script_uid: str = Field(index=True)
    version: str | None = None
    content_json: Any = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

class NormalizedScriptPublic(SQLModel):
    uid: str
    script_uid: str
    version: str | None
    content_json: Any
    created_at: datetime

class ExtractionRun(SQLModel, table=True):
    __tablename__ = "extraction_run"
    uid: str = Field(primary_key=True)
    project_uid: str = Field(index=True)
    script_uid: str = Field(index=True)
    step: int
    status: str | None = None
    error_message: str | None = None
    model_config_data: Any | None = Field(default=None, sa_column=Column("model_config", JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    finished_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))

class ExtractionRunCreate(SQLModel):
    project_uid: str
    script_uid: str
    step: int
    model_config_dict: dict[str, Any] | None = Field(default=None, alias="model_config")

class ExtractionRunPublic(SQLModel):
    uid: str
    project_uid: str
    script_uid: str
    step: int
    status: str | None
    error_message: str | None = None
    created_at: datetime
    finished_at: datetime | None

class ArtifactSnapshot(SQLModel, table=True):
    __tablename__ = "artifact_snapshot"
    uid: str = Field(primary_key=True)
    run_uid: str = Field(index=True)
    content_json: Any = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

class CandidateEntity(SQLModel, table=True):
    __tablename__ = "candidate_entity"
    uid: str = Field(primary_key=True)
    run_uid: str = Field(index=True)
    raw_name: str
    entity_type: str
    confidence: float | None = None
    canonical_asset_uid: str | None = Field(default=None, index=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))


class CandidateEntityCreate(SQLModel):
    run_uid: str
    raw_name: str
    entity_type: str
    confidence: float | None = None

class CandidateEntityUpdate(SQLModel):
    canonical_asset_uid: str | None = None
    entity_type: str | None = None

class CandidateEntityPublic(SQLModel):
    uid: str
    run_uid: str
    raw_name: str
    entity_type: str
    confidence: float | None
    canonical_asset_uid: str | None
    created_at: datetime

class CanonicalAsset(SQLModel, table=True):
    __tablename__ = "canonical_asset"
    __table_args__ = (Index("canonical_asset_project_uid_type_idx", "project_uid", "type"),)
    uid: str = Field(primary_key=True)
    project_uid: str = Field(index=True)
    run_uid: str | None = Field(default=None, index=True)
    name: str
    type: str
    description: str | None = None
    status: str
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))

class CanonicalAssetAlias(SQLModel, table=True):
    __tablename__ = "canonical_asset_alias"
    uid: str = Field(primary_key=True)
    asset_uid: str = Field(index=True)
    alias: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

class CanonicalAssetAliasCreate(SQLModel):
    alias: str

class CanonicalAssetAliasPublic(SQLModel):
    uid: str
    asset_uid: str
    alias: str
    created_at: datetime

class CanonicalAssetCreate(SQLModel):
    project_uid: str
    name: str
    type: str
    description: str | None = None
    aliases: list[str] = []

class CanonicalAssetUpdate(SQLModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None

class CanonicalAssetPublic(SQLModel):
    uid: str
    project_uid: str
    name: str
    type: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    aliases: list[CanonicalAssetAliasPublic] = []
