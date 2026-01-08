import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

JobStatus = Literal["pending", "running", "completed", "failed"]
JobStep = Literal["step1", "step2", "step3"]


class Step2Request(BaseModel):
    project_uid: str
    script_uid: str
    provider: str = "mock"


class Step2Response(BaseModel):
    job_uid: str
    run_uid: str


class JobPublic(BaseModel):
    job_uid: str
    step: JobStep
    status: JobStatus
    run_uid: str | None = None
    error_message: str | None = None
    created_at: datetime

    @classmethod
    def new(cls, *, step: JobStep) -> "JobPublic":
        return cls(
            job_uid=f"job_{uuid.uuid4().hex}",
            step=step,
            status="running",
            created_at=datetime.now(timezone.utc),
        )
