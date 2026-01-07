from fastapi.testclient import TestClient
from app.core.config import settings

def test_canonical_assets(client: TestClient) -> None:
    # 1. Setup Project
    proj_resp = client.post(f"{settings.API_V1_STR}/projects/", json={"name": "Asset Proj"})
    project_uid = proj_resp.json()["uid"]

    # 2. Create Asset
    asset_data = {
        "project_uid": project_uid,
        "name": "Asset 1",
        "type": "person",
        "description": "Desc",
        "aliases": ["A1", "A2"]
    }
    resp = client.post(f"{settings.API_V1_STR}/assets/", json=asset_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Asset 1"
    assert len(data["aliases"]) == 2
    asset_uid = data["uid"]

    # 3. Read Asset
    resp = client.get(f"{settings.API_V1_STR}/assets/{asset_uid}")
    assert resp.status_code == 200
    assert resp.json()["uid"] == asset_uid

    # 4. List Assets
    resp = client.get(f"{settings.API_V1_STR}/assets/?project_uid={project_uid}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 5. Update Asset
    patch_data = {"description": "New Desc"}
    resp = client.patch(f"{settings.API_V1_STR}/assets/{asset_uid}", json=patch_data)
    assert resp.status_code == 200
    assert resp.json()["description"] == "New Desc"

    # 6. Add Alias
    resp = client.post(f"{settings.API_V1_STR}/assets/{asset_uid}/aliases", json={"alias": "A3"})
    assert resp.status_code == 200
    alias_uid = resp.json()["uid"]
    
    # Verify alias added
    resp = client.get(f"{settings.API_V1_STR}/assets/{asset_uid}")
    assert len(resp.json()["aliases"]) == 3

    # 7. Delete Alias
    resp = client.delete(f"{settings.API_V1_STR}/aliases/{alias_uid}")
    assert resp.status_code == 200
    
    # Verify deleted
    resp = client.get(f"{settings.API_V1_STR}/assets/{asset_uid}")
    assert len(resp.json()["aliases"]) == 2
