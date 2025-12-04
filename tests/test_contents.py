"""
Content management endpoint tests.

Tests:
- Create content (success and unauthorized)
- Get all contents
- Get content by ID
- Delete content
"""

from fastapi import status


def get_auth_token(client, username="testuser", password="testpassword123"):
    """Helper: Get JWT token for authenticated requests."""
    response = client.post(
        "/api/login",
        json={"username": username, "password": password}
    )
    return response.json()["access_token"]


def test_create_content_success(client, test_user):
    """Test authenticated user can create content."""
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
    """Test unauthenticated requests are rejected."""
    response = client.post(
        "/api/contents",
        json={"text": "Unauthorized content"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_contents_success(client, test_user):
    """Test user can retrieve their content list."""
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
    """Test user can retrieve specific content by ID."""
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
    """Test user can delete their content."""
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

