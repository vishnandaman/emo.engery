"""
Unit tests for content management endpoints.

Tests cover:
- Creating content
- Retrieving content
- Deleting content
- Authentication requirements
"""

import pytest
from fastapi import status


def get_auth_token(client, username="testuser", password="testpassword123"):
    """
    Helper function to get authentication token.
    
    Args:
        client: Test client
        username: Username for login
        password: Password for login
    
    Returns:
        str: JWT access token
    """
    response = client.post(
        "/api/login",
        json={"username": username, "password": password}
    )
    return response.json()["access_token"]


def test_create_content_success(client, test_user):
    """
    Test successful content creation.
    
    This test:
    1. Authenticates as test_user
    2. Creates new content
    3. Verifies content is created with correct data
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/contents",
        json={"text": "This is a test content for AI analysis."},
        headers=headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["text"] == "This is a test content for AI analysis."
    assert data["id"] is not None
    assert data["user_id"] == test_user.id


def test_create_content_unauthorized(client):
    """
    Test content creation without authentication.
    
    This test verifies that unauthenticated requests
    are rejected with 401 Unauthorized.
    """
    response = client.post(
        "/api/contents",
        json={"text": "Unauthorized content"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_contents_success(client, test_user):
    """
    Test retrieving user's content list.
    
    This test:
    1. Creates content
    2. Retrieves all contents
    3. Verifies the content is in the list
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create content
    client.post(
        "/api/contents",
        json={"text": "First content"},
        headers=headers
    )
    
    # Get all contents
    response = client.get("/api/contents", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert len(data["contents"]) >= 1


def test_get_content_by_id(client, test_user):
    """
    Test retrieving specific content by ID.
    
    This test:
    1. Creates content
    2. Retrieves it by ID
    3. Verifies correct content is returned
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create content
    create_response = client.post(
        "/api/contents",
        json={"text": "Specific content"},
        headers=headers
    )
    content_id = create_response.json()["id"]
    
    # Get content by ID
    response = client.get(f"/api/contents/{content_id}", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == content_id
    assert data["text"] == "Specific content"


def test_delete_content_success(client, test_user):
    """
    Test successful content deletion.
    
    This test:
    1. Creates content
    2. Deletes it
    3. Verifies it's deleted (404 on retrieval)
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create content
    create_response = client.post(
        "/api/contents",
        json={"text": "Content to delete"},
        headers=headers
    )
    content_id = create_response.json()["id"]
    
    # Delete content
    delete_response = client.delete(f"/api/contents/{content_id}", headers=headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify content is deleted
    get_response = client.get(f"/api/contents/{content_id}", headers=headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

