"""
Test suite for authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db.database import init_db, get_db, SessionLocal
from db import auth_crud

client = TestClient(app)

# Test data
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123456",
    "full_name": "Test User",
}

TEST_LOGIN = {
    "email": "test@example.com",
    "password": "testpass123456",
}


@pytest.fixture(scope="module", autouse=True)
def setup():
    """Initialize database before tests"""
    init_db()
    yield
    # Cleanup
    db = SessionLocal()
    try:
        # Delete test user
        user = auth_crud.get_user_by_email(db, TEST_USER["email"])
        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_signup_success(self):
        """Test successful user signup"""
        response = client.post("/auth/signup", json=TEST_USER)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == TEST_USER["email"]
        assert data["username"] == TEST_USER["username"]
        assert "password" not in data

    def test_signup_duplicate_email(self):
        """Test signup with duplicate email"""
        # First signup
        client.post("/auth/signup", json=TEST_USER)
        
        # Duplicate signup
        response = client.post("/auth/signup", json={
            **TEST_USER,
            "username": "different_user",
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_signup_duplicate_username(self):
        """Test signup with duplicate username"""
        # First signup
        client.post("/auth/signup", json=TEST_USER)
        
        # Duplicate username
        response = client.post("/auth/signup", json={
            **TEST_USER,
            "email": "different@example.com",
        })
        assert response.status_code == 400

    def test_login_success(self):
        """Test successful login"""
        # Create user first
        client.post("/auth/signup", json=TEST_USER)
        
        # Login
        response = client.post("/auth/login", json=TEST_LOGIN)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800  # 30 minutes
        assert data["user"]["email"] == TEST_USER["email"]

    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "anypassword",
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_invalid_password(self):
        """Test login with wrong password"""
        # Create user first
        client.post("/auth/signup", json=TEST_USER)
        
        # Login with wrong password
        response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_get_current_user(self):
        """Test getting current user profile"""
        # Create and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json=TEST_LOGIN)
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER["email"]
        assert data["username"] == TEST_USER["username"]
        assert data["full_name"] == TEST_USER["full_name"]

    def test_get_current_user_no_token(self):
        """Test getting current user without token"""
        response = client.get("/auth/me")
        assert response.status_code == 403

    def test_change_password_success(self):
        """Test changing password"""
        # Create and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json=TEST_LOGIN)
        token = login_response.json()["access_token"]
        
        # Change password
        response = client.post(
            "/auth/change-password",
            json={
                "old_password": TEST_USER["password"],
                "new_password": "newpass123456",
                "confirm_password": "newpass123456",
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "success" in response.json()["status"]

    def test_change_password_wrong_old_password(self):
        """Test changing password with wrong old password"""
        # Create and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json=TEST_LOGIN)
        token = login_response.json()["access_token"]
        
        # Change password with wrong old password
        response = client.post(
            "/auth/change-password",
            json={
                "old_password": "wrongpassword",
                "new_password": "newpass123456",
                "confirm_password": "newpass123456",
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    def test_change_password_mismatch(self):
        """Test changing password with mismatched new passwords"""
        # Create and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json=TEST_LOGIN)
        token = login_response.json()["access_token"]
        
        # Change password with mismatched new passwords
        response = client.post(
            "/auth/change-password",
            json={
                "old_password": TEST_USER["password"],
                "new_password": "newpass123456",
                "confirm_password": "differentpass123",
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400

    def test_refresh_token_success(self):
        """Test refreshing access token"""
        # Create and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json=TEST_LOGIN)
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == refresh_token  # Same refresh token

    def test_refresh_token_invalid(self):
        """Test refreshing with invalid token"""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401

    def test_refresh_token_missing(self):
        """Test refreshing without refresh token"""
        response = client.post(
            "/auth/refresh",
            json={}
        )
        assert response.status_code == 400

    def test_logout_success(self):
        """Test logout"""
        # Create and login
        client.post("/auth/signup", json=TEST_USER)
        login_response = client.post("/auth/login", json=TEST_LOGIN)
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "success" in response.json()["status"]

    def test_logout_no_token(self):
        """Test logout without token"""
        response = client.post("/auth/logout")
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
