from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings

def test_create_project(client: TestClient) -> None:
    data = {"name": "Test Project", "description": "A test description"}
    response = client.post(
        f"{settings.API_V1_STR}/projects/",
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "uid" in content
    assert content["uid"].startswith("proj_")

def test_read_projects(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/projects/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_project(client: TestClient) -> None:
    # First create one
    data = {"name": "Test Project 2", "description": "Desc"}
    create_resp = client.post(
        f"{settings.API_V1_STR}/projects/",
        json=data,
    )
    uid = create_resp.json()["uid"]
    
    response = client.get(f"{settings.API_V1_STR}/projects/{uid}")
    assert response.status_code == 200
    content = response.json()
    assert content["uid"] == uid
    assert content["name"] == data["name"]
