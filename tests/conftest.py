import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Pytest fixture providing a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_email():
    """Pytest fixture providing a test email address"""
    return "test.student@mergington.edu"


@pytest.fixture
def activity_name():
    """Pytest fixture providing a valid activity name"""
    return "Chess Club"


@pytest.fixture
def reset_activities():
    """Pytest fixture to reset activities to initial state after each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    yield
    # Reset after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()
