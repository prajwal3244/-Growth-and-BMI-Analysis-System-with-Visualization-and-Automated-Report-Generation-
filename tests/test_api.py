"""Integration tests for the FastAPI backend (feature #15: API tests)."""

from __future__ import annotations

import os

import pytest

# Use an isolated on-disk SQLite DB per test session.
os.environ.setdefault("GROWTHAI_DATABASE_URL", "sqlite:///./test_growthai.db")

from fastapi.testclient import TestClient  # noqa: E402

from growthai.api.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    # Release the SQLite file (Windows locks it while the pool is open) before removing.
    from growthai.db.base import engine

    engine.dispose()
    try:
        if os.path.exists("test_growthai.db"):
            os.remove("test_growthai.db")
    except PermissionError:
        pass  # best-effort cleanup; file is gitignored


@pytest.fixture(scope="module")
def auth_headers(client):
    email = "pytest_parent@demo.com"
    client.post("/auth/register", json={"email": email, "password": "secret123", "role": "parent"})
    r = client.post("/auth/login", data={"username": email, "password": "secret123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}


def test_analyze_anonymous(client):
    r = client.post("/analysis", json={"age_months": 96, "height_cm": 128, "weight_kg": 26, "gender": "M"})
    assert r.status_code == 200
    data = r.json()
    assert "assessment" in data and "forecasts" in data and "risk" in data and "nutrition" in data
    assert data["assessment"]["category"]


def test_analyze_rejects_invalid_input(client):
    r = client.post("/analysis", json={"age_months": 999, "height_cm": 128, "weight_kg": 26, "gender": "M"})
    assert r.status_code == 422


def test_protected_route_requires_auth(client):
    assert client.get("/patients").status_code == 401


def test_patient_lifecycle_and_history(client, auth_headers):
    r = client.post("/patients", json={"name": "Test Child", "gender": "F"}, headers=auth_headers)
    assert r.status_code == 201
    pid = r.json()["id"]

    client.post(
        "/analysis",
        json={"age_months": 120, "height_cm": 138, "weight_kg": 32, "gender": "F",
              "name": "Test Child", "patient_id": pid, "save": True},
    )
    hist = client.get(f"/patients/{pid}/history", headers=auth_headers).json()
    assert len(hist["timeline"]) == 1
    assert hist["timeline"][0]["category"]


def test_chat_endpoint(client):
    r = client.post("/chat", json={"question": "What does BMI mean?"})
    assert r.status_code == 200
    assert r.json()["provider"] == "offline-rag"
    assert "BMI" in r.json()["answer"]


def test_report_generation(client):
    r = client.post("/reports", json={"age_months": 96, "height_cm": 128, "weight_kg": 26, "gender": "M", "name": "R"})
    assert r.status_code == 200
    assert r.json()["html_available"] is True
