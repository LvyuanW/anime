import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import Project, ProjectCreate, ProjectPublic, Script, ScriptCreate, ScriptListPublic

router = APIRouter()

@router.post("/", response_model=ProjectPublic)
def create_project(*, session: SessionDep, project_in: ProjectCreate) -> Any:
    """
    Create a new entity extraction project.
    """
    project = Project.model_validate(project_in, update={"uid": f"proj_{uuid.uuid4().hex}"})
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.get("/", response_model=list[ProjectPublic])
def read_projects(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve projects.
    """
    statement = select(Project).offset(skip).limit(limit)
    projects = session.exec(statement).all()
    return projects

@router.get("/{uid}", response_model=ProjectPublic)
def read_project(*, session: SessionDep, uid: str) -> Any:
    """
    Get project by ID.
    """
    project = session.get(Project, uid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/{project_uid}/scripts/", response_model=ScriptListPublic)
def create_project_script(*, session: SessionDep, project_uid: str, script_in: ScriptCreate) -> Any:
    """
    Upload a script to a project.
    """
    project = session.get(Project, project_uid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    script = Script.model_validate(script_in, update={
        "uid": f"script_{uuid.uuid4().hex}",
        "project_uid": project_uid
    })
    session.add(script)
    session.commit()
    session.refresh(script)
    return script

@router.get("/{project_uid}/scripts/", response_model=list[ScriptListPublic])
def read_project_scripts(*, session: SessionDep, project_uid: str, skip: int = 0, limit: int = 100) -> Any:
    """
    Get all scripts for a project.
    """
    statement = select(Script).where(Script.project_uid == project_uid).offset(skip).limit(limit)
    scripts = session.exec(statement).all()
    return scripts
