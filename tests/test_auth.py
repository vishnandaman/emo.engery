"""
Authentication endpoint tests.

Tests:
- User signup (success and duplicate username)
- User login (success and invalid credentials)
"""

from fastapi import status


def test_signup_success(client):
    """Test successful user registration returns JWT token."""
    response = client.post(
        "/api/signup",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_signup_duplicate_username(client):
    """Test that duplicate username registration is rejected."""
    # Create first user
    client.post(
        "/api/signup",
        json={
            "username": "duplicate",
            "email": "first@example.com",
            "password": "password123"
        }
    )
    
    # Try to create user with same username
    response = client.post(
        "/api/signup",
        json={
            "username": "duplicate",
            "email": "second@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    """Test successful login returns JWT token."""
    response = client.post(
        "/api/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    """Test that incorrect password is rejected."""
    response = client.post(
        "/api/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()

