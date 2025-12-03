"""
Database models (SQLAlchemy ORM models).

These classes represent database tables. SQLAlchemy automatically
creates tables based on these model definitions.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class SentimentType(str, enum.Enum):
    """
    Enumeration for sentiment types.
    
    Enums ensure only valid values can be stored in the database.
    """
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"


class User(Base):
    """
    User model - stores user account information.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        username: Unique username for login
        email: Unique email address
        hashed_password: Password hash (never store plain passwords!)
        created_at: Timestamp when user was created
    """
    __tablename__ = "users"  # Table name in database
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Content(Base):
    """
    Content model - stores user-submitted text content and analysis results.
    
    Attributes:
        id: Primary key
        user_id: Foreign key linking to User table
        text: The original text content submitted by user
        summary: Generated summary (populated after processing)
        sentiment: Detected sentiment (Positive/Negative/Neutral)
        created_at: When content was created
        updated_at: When content was last updated
    """
    __tablename__ = "contents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Foreign key to users table
    text = Column(Text, nullable=False)  # Text can be long, so use Text type
    summary = Column(Text, nullable=True)  # Will be populated by AI
    sentiment = Column(SQLEnum(SentimentType), nullable=True)  # Enum for type safety
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Auto-update on change

