import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)
initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    yield
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert expected_activity in data
    assert data[expected_activity]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert data[expected_activity]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    participant_email = "student@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": participant_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {participant_email} for {activity_name}"}
    assert participant_email in activities[activity_name]["participants"]


def test_signup_for_activity_rejects_duplicate_registration():
    # Arrange
    activity_name = "Chess Club"
    participant_email = "student@example.com"

    client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": participant_email},
    )

    # Act
    duplicate_response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": participant_email},
    )

    # Assert
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"].count(participant_email) == 1


def test_remove_participant_from_activity():
    # Arrange
    activity_name = "Chess Club"
    participant_email = "michael@mergington.edu"
    assert participant_email in activities[activity_name]["participants"]

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(participant_email)}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {participant_email} from {activity_name}"}
    assert participant_email not in activities[activity_name]["participants"]


def test_remove_non_registered_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    participant_email = "not-signed-up@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(participant_email)}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not registered"
