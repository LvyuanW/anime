from fastapi.testclient import TestClient
from app.core.config import settings

def test_create_and_read_run(client: TestClient) -> None:
    # 1. Setup Project & Script
    proj_data = {"name": "Proj Run", "description": "Desc"}
    proj_resp = client.post(f"{settings.API_V1_STR}/projects/", json=proj_data)
    project_uid = proj_resp.json()["uid"]
    
    script_data = {"name": "Ep1", "content": "..."}
    script_resp = client.post(f"{settings.API_V1_STR}/projects/{project_uid}/scripts/", json=script_data)
    script_uid = script_resp.json()["uid"]

    # 2. Create Run
    run_data = {
        "project_uid": project_uid,
        "script_uid": script_uid,
        "step": 1,
        "model_config": {"model": "gpt-4"}
    }
    run_resp = client.post(f"{settings.API_V1_STR}/runs/", json=run_data)
    assert run_resp.status_code == 200
    run_json = run_resp.json()
    assert run_json["status"] == "running"
    assert run_json["step"] == 1
    run_uid = run_json["uid"]

    # 3. Read Run
    detail_resp = client.get(f"{settings.API_V1_STR}/runs/{run_uid}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["uid"] == run_uid

    # 4. List Runs for Script
    list_resp = client.get(f"{settings.API_V1_STR}/scripts/{script_uid}/runs")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) >= 1
    assert runs[0]["uid"] == run_uid
