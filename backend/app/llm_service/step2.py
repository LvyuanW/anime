from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, cast

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.llm_service.prompts import load_prompt
from app.llm_service.providers.base import LLMProvider
from app.llm_service.providers.mock import MockProvider
from app.llm_service.providers.openai_compat import OpenAICompatProvider
from app.models import (
    ArtifactSnapshot,
    CandidateEntity,
    ExtractionRun,
    NormalizedScript,
    Script,
)


def _get_engine() -> Engine:
    return create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def _chunk_by_scene(content_json: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for row in content_json:
        if str(row.get("type") or "") == "scene_header" and current:
            chunks.append(current)
            current = []
        current.append(row)
    if current:
        chunks.append(current)
    return chunks


def run_step2_candidate_extraction(*, project_uid: str, script_uid: str, provider_name: str = "mock") -> str:
    prompt = load_prompt("资产抽取工序02.txt")
    provider: LLMProvider
    if provider_name == "mock":
        provider = MockProvider()
    elif provider_name == "gpt":
        provider = OpenAICompatProvider()
    else:
        raise ValueError("Unsupported provider")

    engine = _get_engine()
    with Session(engine) as session:
        script = session.get(Script, script_uid)
        if not script:
            raise ValueError("Script not found")
        normalized = session.exec(
            select(NormalizedScript)
            .where(NormalizedScript.script_uid == script_uid)
            .order_by(cast(Any, NormalizedScript.created_at).desc())
        ).first()
        if not normalized:
            raise ValueError("Normalized script not found; run Step1 first")

        run_uid = f"run_{uuid.uuid4().hex}"
        run = ExtractionRun(
            uid=run_uid,
            project_uid=project_uid,
            script_uid=script_uid,
            step=2,
            status="running",
            model_config_data={"provider": provider.name, "prompt_sha256": prompt.sha256},
        )
        session.add(run)
        session.commit()

        content_json = normalized.content_json
        if not isinstance(content_json, list):
            raise ValueError("Normalized script content_json must be a list")

        chunks = _chunk_by_scene([x for x in content_json if isinstance(x, dict)])
        all_candidates: dict[tuple[str, str], dict[str, Any]] = {}
        raw_outputs: list[dict[str, Any]] = []

        for chunk in chunks:
            chunk_json = json.dumps(chunk, ensure_ascii=False)
            raw = provider.extract_candidates(prompt=prompt.content, normalized_chunk_json=chunk_json)
            raw_outputs.append({"chunk_size": len(chunk), "raw_output": raw})
            parsed = json.loads(raw)
            candidates = parsed.get("candidates", [])
            if not isinstance(candidates, list):
                continue
            for c in candidates:
                if not isinstance(c, dict):
                    continue
                raw_name = str(c.get("raw_name") or "").strip()
                entity_type = str(c.get("entity_type") or "").strip()
                if not raw_name or entity_type not in {"person", "scene", "prop", "other"}:
                    continue
                confidence = c.get("confidence")
                if confidence is not None:
                    try:
                        confidence = float(confidence)
                    except Exception:
                        confidence = None
                all_candidates.setdefault(
                    (raw_name, entity_type),
                    {"raw_name": raw_name, "entity_type": entity_type, "confidence": confidence},
                )

        created_candidates: list[dict[str, Any]] = []
        for (raw_name, entity_type), c in all_candidates.items():
            cand_uid = f"cand_{uuid.uuid4().hex}"
            session.add(
                CandidateEntity(
                    uid=cand_uid,
                    run_uid=run_uid,
                    raw_name=raw_name,
                    entity_type=entity_type,
                    confidence=c.get("confidence"),
                )
            )
            created_candidates.append({"uid": cand_uid, "raw_name": raw_name, "entity_type": entity_type})

        snapshot = ArtifactSnapshot(
            uid=f"art_{uuid.uuid4().hex}",
            run_uid=run_uid,
            content_json={
                "step": 2,
                "provider": provider.name,
                "prompt_sha256": prompt.sha256,
                "script_uid": script_uid,
                "normalized_script_uid": normalized.uid,
                "chunk_count": len(chunks),
                "candidates": created_candidates,
                "raw_outputs": raw_outputs,
            },
            created_at=datetime.now(timezone.utc),
        )
        session.add(snapshot)

        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        session.add(run)
        session.commit()

        return run_uid
