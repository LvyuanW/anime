import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from app.models import CandidateEntity, CandidateEvidence

def test_candidates_and_evidences(client: TestClient, db: Session) -> None:
    # 1. Setup Data
    # Manually create run/project/script to save time or via API
    # Let's use API
    proj_resp = client.post(f"{settings.API_V1_STR}/projects/", json={"name": "Cand Proj"})
    project_uid = proj_resp.json()["uid"]
    script_resp = client.post(f"{settings.API_V1_STR}/projects/{project_uid}/scripts/", json={"name": "S1", "content": "."})
    script_uid = script_resp.json()["uid"]
    run_resp = client.post(f"{settings.API_V1_STR}/runs/", json={"project_uid": project_uid, "script_uid": script_uid, "step": 2})
    run_uid = run_resp.json()["uid"]

    # Manually insert candidate via DB for test setup if there is no "Create Candidate" API (it comes from background process usually)
    # But wait, 4.1 is GET, so we need data there.
    # We can create candidate manually in DB.
    cand_uid = f"cand_{uuid.uuid4().hex}"
    cand = CandidateEntity(
        uid=cand_uid,
        run_uid=run_uid,
        raw_name="Old Name",
        entity_type="person",
        confidence=0.9
    )
    db.add(cand)
    db.commit()
    
    # Add evidence
    ev_uid_manual = f"ev_{uuid.uuid4().hex}"
    ev = CandidateEvidence(
        uid=ev_uid_manual,
        candidate_uid=cand_uid,
        line_id="L1",
        quote="Quote"
    )
    db.add(ev)
    db.commit()

    # 2. Get Candidates
    resp = client.get(f"{settings.API_V1_STR}/runs/{run_uid}/candidates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["uid"] == cand_uid
    assert len(data[0]["evidences"]) == 1
    assert data[0]["evidences"][0]["uid"] == ev_uid_manual

    # 3. Update Candidate
    patch_data = {"canonical_asset_uid": "asset_123", "entity_type": "prop"}
    resp = client.patch(f"{settings.API_V1_STR}/candidates/{cand_uid}", json=patch_data)
    assert resp.status_code == 200
    assert resp.json()["canonical_asset_uid"] == "asset_123"
    assert resp.json()["entity_type"] == "prop"

    # 4. Add Evidence
    ev_data = {"line_id": "L2", "quote": "New Quote"}
    resp = client.post(f"{settings.API_V1_STR}/candidates/{cand_uid}/evidences", json=ev_data)
    assert resp.status_code == 200
    ev_uid = resp.json()["uid"]
    
    # Verify added
    resp = client.get(f"{settings.API_V1_STR}/runs/{run_uid}/candidates")
    assert len(resp.json()[0]["evidences"]) == 2

    # 5. Delete Evidence
    resp = client.delete(f"{settings.API_V1_STR}/evidences/{ev_uid}")
    assert resp.status_code == 200
    
    # Verify deleted
    resp = client.get(f"{settings.API_V1_STR}/runs/{run_uid}/candidates")
    evs = resp.json()[0]["evidences"]
    assert len(evs) == 1
    assert evs[0]["uid"] == ev_uid_manual

    # 6. Delete Candidate
    resp = client.delete(f"{settings.API_V1_STR}/candidates/{cand_uid}")
    assert resp.status_code == 200
    
    # Verify candidate deleted
    resp = client.get(f"{settings.API_V1_STR}/runs/{run_uid}/candidates")
    assert len(resp.json()) == 0
