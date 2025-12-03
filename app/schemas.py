"""
Pydantic schemas for request/response validation.

Pydantic ensures data types are correct and validates input/output.
These schemas define the structure of API requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models import SentimentType


# ============ Authentication Schemas ============

class UserSignup(BaseModel):
    """
    Schema for user registration request.
    
    Attributes:
        username: Must be unique, used for login (3-50 characters)
        email: Must be valid email format and unique
        password: Plain text password (will be hashed before storage)
                  Minimum 6 characters, maximum 200 characters
                  Note: Passwords longer than 72 bytes are automatically
                  pre-hashed with SHA256 before bcrypt hashing
    """
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=200, description="Password (6-200 characters)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password length.
        
        Ensures password is between 6 and 200 characters.
        Longer passwords are handled automatically by pre-hashing.
        """
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v) > 200:
            raise ValueError('Password cannot exceed 200 characters')
        return v


class UserLogin(BaseModel):
    """
    Schema for user login request.
    
    Attributes:
        username: User's username
        password: User's password
    """
    username: str
    password: str


class Token(BaseModel):
    """
    Schema for JWT token response.
    
    Attributes:
        access_token: JWT token string
        token_type: Usually "bearer"
    """
    access_token: str
    token_type: str


# ============ Content Schemas ============

class ContentCreate(BaseModel):
    """
    Schema for creating new content.
    
    Attributes:
        text: The text content to be analyzed
    """
    text: str


class ContentResponse(BaseModel):
    """
    Schema for content response (what we return to the user).
    
    Attributes:
        id: Content ID
        text: Original text
        summary: AI-generated summary
        sentiment: Detected sentiment
        created_at: Creation timestamp
        updated_at: Last update timestamp
    
    Config:
        from_attributes: Allows conversion from SQLAlchemy models
    """
    id: int
    text: str
    summary: Optional[str]
    sentiment: Optional[SentimentType]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Allows Pydantic to read from SQLAlchemy models


class ContentListResponse(BaseModel):
    """
    Schema for list of contents response.
    
    Attributes:
        contents: List of ContentResponse objects
        total: Total number of contents
    """
    contents: list[ContentResponse]
    total: int

