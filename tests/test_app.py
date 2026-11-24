from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        test_client.post(
            "/auth/login",
            params={
                "email": "admin@mergington.edu",
                "password": "mergington123",
            },
        )
        yield test_client


def test_root_redirects_to_static_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_participants = [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]

    # Act
    response = client.get("/activities")
    response_data = response.json()

    # Assert
    assert response.status_code == 200
    assert "Chess Club" in response_data
    assert response_data["Chess Club"]["participants"] == expected_participants


def test_signup_adds_participant(client):
    # Arrange
    email = "test.student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_participant_not_signed_up(client):
    # Arrange
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_activities_require_sign_in():
    with TestClient(app) as anonymous_client:
        response = anonymous_client.get("/activities")

    assert response.status_code == 401
    assert response.json()["detail"] == "Sign-in required"


def test_login_rejects_invalid_credentials():
    with TestClient(app) as anonymous_client:
        response = anonymous_client.post(
            "/auth/login",
            params={
                "email": "admin@mergington.edu",
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_chat_requires_sign_in():
    with TestClient(app) as anonymous_client:
        response = anonymous_client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Sign-in required"


def test_chat_returns_agent_reply(client, monkeypatch):
    class FakeAgent:
        async def run(self, prompt):
            assert "User: What activities are available?" in prompt
            return SimpleNamespace(text="Chess and art are available.")

    monkeypatch.setattr(app_module, "_chat_agent", FakeAgent())
    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "What activities are available?"}]},
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "Chess and art are available."}
