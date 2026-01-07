from fastapi.testclient import TestClient
from app.core.config import settings

def test_create_and_read_script(client: TestClient) -> None:
    # 1. Create Project
    proj_data = {"name": "Proj for Script", "description": "Desc"}
    proj_resp = client.post(f"{settings.API_V1_STR}/projects/", json=proj_data)
    assert proj_resp.status_code == 200
    project_uid = proj_resp.json()["uid"]

    # 2. Create Script
    script_data = {"name": "Ep1", "content": "INT. ROOM - DAY"}
    script_resp = client.post(f"{settings.API_V1_STR}/projects/{project_uid}/scripts/", json=script_data)
    assert script_resp.status_code == 200
    script_json = script_resp.json()
    assert script_json["name"] == script_data["name"]
    # List view shouldn't have content
    assert "content" not in script_json 
    script_uid = script_json["uid"]

    # 3. Read Script Detail
    detail_resp = client.get(f"{settings.API_V1_STR}/scripts/{script_uid}")
    assert detail_resp.status_code == 200
    detail_json = detail_resp.json()
    assert detail_json["content"] == script_data["content"]
    
    # 4. List Scripts
    list_resp = client.get(f"{settings.API_V1_STR}/projects/{project_uid}/scripts/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

def test_read_normalized_script_not_found(client: TestClient) -> None:
    # Need a script first
    proj_data = {"name": "Proj for Norm", "description": "Desc"}
    proj_resp = client.post(f"{settings.API_V1_STR}/projects/", json=proj_data)
    project_uid = proj_resp.json()["uid"]
    script_data = {"name": "Ep1", "content": "..."}
    script_resp = client.post(f"{settings.API_V1_STR}/projects/{project_uid}/scripts/", json=script_data)
    script_uid = script_resp.json()["uid"]

    # Try get normalized
    norm_resp = client.get(f"{settings.API_V1_STR}/scripts/{script_uid}/normalized")
    assert norm_resp.status_code == 404
