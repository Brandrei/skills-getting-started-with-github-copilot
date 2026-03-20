import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Test suite for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: No setup needed
        Act: Make a GET request to root
        Assert: Response should redirect to /static/index.html
        """
        # Arrange
        # No setup needed
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers.get("location", "")


class TestGetActivitiesEndpoint:
    """Test suite for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: We know the app has 10 activities
        Act: Make a GET request to /activities
        Assert: Response contains all activities with correct structure
        """
        # Arrange
        expected_activity_count = 10
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(activities) == expected_activity_count
        assert "Chess Club" in activities
        assert "Programming Class" in activities
    
    def test_activity_has_required_fields(self, client):
        """
        Arrange: Know the structure of an activity
        Act: Get activities and check one
        Assert: Activity has all required fields
        """
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        # Assert
        assert all(field in chess_club for field in required_fields)
        assert isinstance(chess_club["participants"], list)
        assert isinstance(chess_club["max_participants"], int)
    
    def test_activities_show_current_participant_counts(self, client):
        """
        Arrange: Chess Club has 2 participants initially
        Act: Get activities
        Assert: Participant count matches for Chess Club
        """
        # Arrange
        expected_participants_count = 2  # michael@mergington.edu, daniel@mergington.edu
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        # Assert
        assert len(chess_club["participants"]) == expected_participants_count


class TestSignupEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_adds_participant(self, client, reset_activities, sample_email, activity_name):
        """
        Arrange: Student not yet registered, activity exists
        Act: Submit signup request
        Assert: Student is added to participants, response is success
        """
        # Arrange
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify participant was added
        updated_activities = client.get("/activities").json()
        updated_count = len(updated_activities[activity_name]["participants"])
        assert updated_count == initial_count + 1
        assert sample_email in updated_activities[activity_name]["participants"]
    
    def test_signup_fails_activity_not_found(self, client, sample_email):
        """
        Arrange: Invalid activity name
        Act: Submit signup for non-existent activity
        Assert: Response is 404 not found
        """
        # Arrange
        invalid_activity = "Invalid Activity That Does Not Exist"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": sample_email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_fails_duplicate_registration(self, client, reset_activities, activity_name):
        """
        Arrange: Student already registered for activity
        Act: Try to signup same student again
        Assert: Response is 400 bad request with appropriate message
        """
        # Arrange
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_with_different_email_formats(self, client, reset_activities, activity_name):
        """
        Arrange: Various email formats
        Act: Attempt signup with different email formats
        Assert: All are accepted (no email validation on backend)
        """
        # Arrange
        test_emails = ["simple@test.com", "user+tag@example.org", "no-validation-here"]
        
        # Act & Assert
        for email in test_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200, f"Failed for email: {email}"


class TestRemoveParticipantEndpoint:
    """Test suite for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_successful(self, client, reset_activities, activity_name):
        """
        Arrange: Participant exists in activity
        Act: Send DELETE request to remove participant
        Assert: Participant is removed, response is success
        """
        # Arrange
        email_to_remove = "michael@mergington.edu"  # In Chess Club
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        
        # Verify participant was removed
        updated_activities = client.get("/activities").json()
        updated_count = len(updated_activities[activity_name]["participants"])
        assert updated_count == initial_count - 1
        assert email_to_remove not in updated_activities[activity_name]["participants"]
    
    def test_remove_participant_activity_not_found(self, client):
        """
        Arrange: Invalid activity name
        Act: Try to remove participant from non-existent activity
        Assert: Response is 404 not found
        """
        # Arrange
        invalid_activity = "Nonexistent Activity"
        email = "test@example.com"
        
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_remove_participant_not_in_activity(self, client, activity_name):
        """
        Arrange: Participant doesn't exist in activity
        Act: Try to remove non-existent participant
        Assert: Response is 404 not found
        """
        # Arrange
        email_not_in_activity = "nonexistent@example.com"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email_not_in_activity}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_remove_participant_then_can_signup_again(self, client, reset_activities, activity_name):
        """
        Arrange: Participant is in activity, then removed
        Act: Remove participant, then try to signup again
        Assert: Signup succeeds after removal
        """
        # Arrange
        email = "michael@mergington.edu"
        
        # Act - Remove participant
        response_delete = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert first removal works
        assert response_delete.status_code == 200
        
        # Act - Try to signup again
        response_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert signup succeeds
        assert response_signup.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
