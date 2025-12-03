"""
Unit tests for authentication endpoints.

Tests cover:
- User registration (signup)
- User login
- Token generation
- Error handling
"""

import pytest
from fastapi import status


def test_signup_success(client):
    """
    Test successful user registration.
    
    This test:
    1. Sends a POST request to /api/signup
    2. Verifies the response status is 201 Created
    3. Verifies a JWT token is returned
    """
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
    """
    Test registration with duplicate username.
    
    This test verifies that the API correctly rejects
    duplicate usernames with a 400 Bad Request error.
    """
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
    """
    Test successful user login.
    
    This test:
    1. Uses the test_user fixture (pre-created user)
    2. Sends login request with correct credentials
    3. Verifies JWT token is returned
    """
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
    """
    Test login with incorrect password.
    
    This test verifies that the API correctly rejects
    invalid credentials with a 401 Unauthorized error.
    """
    response = client.post(
        "/api/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()

