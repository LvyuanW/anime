from fastapi import FastAPI, HTTPException

from app.llm_service.models import JobPublic, Step2Request, Step2Response
from app.llm_service.step2 import run_step2_candidate_extraction

app = FastAPI(title="LLM Orchestrator", version="0.1.0")

_jobs: dict[str, JobPublic] = {}


@app.post("/jobs/step2", response_model=Step2Response)
def create_step2_job(payload: Step2Request) -> Step2Response:
    job = JobPublic.new(step="step2")
    _jobs[job.job_uid] = job
    try:
        run_uid = run_step2_candidate_extraction(
            project_uid=payload.project_uid,
            script_uid=payload.script_uid,
            provider_name=payload.provider,
        )
    except ValueError as e:
        job.status = "failed"
        job.error_message = str(e)
        _jobs[job.job_uid] = job
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        job.status = "failed"
        job.error_message = "Internal error"
        _jobs[job.job_uid] = job
        raise HTTPException(status_code=500, detail="Internal error") from e

    job.status = "completed"
    job.run_uid = run_uid
    _jobs[job.job_uid] = job
    return Step2Response(job_uid=job.job_uid, run_uid=run_uid)


@app.get("/jobs/{job_uid}", response_model=JobPublic)
def read_job(job_uid: str) -> JobPublic:
    job = _jobs.get(job_uid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

