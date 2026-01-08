import uuid

from sqlmodel import Session, delete, select

from app.llm_service.step2 import run_step2_candidate_extraction
from app.models import (
    ArtifactSnapshot,
    CandidateEntity,
    ExtractionRun,
    NormalizedScript,
    Project,
    Script,
)


def test_step2_poc_creates_candidates_and_snapshot(db: Session) -> None:
    project_uid = f"proj_llm_{uuid.uuid4().hex}"
    script_uid = f"script_llm_{uuid.uuid4().hex}"
    normalized_uid = f"norm_llm_{uuid.uuid4().hex}"
    run_uid: str | None = None

    try:
        db.add(Project(uid=project_uid, name="P", description=None))
        db.add(Script(uid=script_uid, project_uid=project_uid, name="S", content="x"))
        db.add(
            NormalizedScript(
                uid=normalized_uid,
                script_uid=script_uid,
                version="v1",
                content_json=[
                    {"line_id": "S01.L01", "text": "（日，内，警局）", "type": "scene_header"},
                    {"line_id": "S01.L02", "text": "老张：这案子不好办。", "type": "dialogue"},
                    {"line_id": "S01.L03", "text": "小李：我去查。", "type": "dialogue"},
                ],
            )
        )
        db.commit()

        run_uid = run_step2_candidate_extraction(
            project_uid=project_uid,
            script_uid=script_uid,
            provider_name="mock",
        )

        db.commit()
        db.expire_all()

        candidates = db.exec(select(CandidateEntity).where(CandidateEntity.run_uid == run_uid)).all()
        assert len(candidates) >= 2

        snapshots = db.exec(select(ArtifactSnapshot).where(ArtifactSnapshot.run_uid == run_uid)).all()
        assert len(snapshots) == 1
    finally:
        db.rollback()
        if run_uid:
            db.exec(delete(CandidateEntity).where(CandidateEntity.run_uid == run_uid))
            db.exec(delete(ArtifactSnapshot).where(ArtifactSnapshot.run_uid == run_uid))
            db.exec(delete(ExtractionRun).where(ExtractionRun.uid == run_uid))
        db.exec(delete(NormalizedScript).where(NormalizedScript.uid == normalized_uid))
        db.exec(delete(Script).where(Script.uid == script_uid))
        db.exec(delete(Project).where(Project.uid == project_uid))
        db.commit()
