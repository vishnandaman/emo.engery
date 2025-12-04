"""
Test configuration and fixtures.

This file sets up the test database (MySQL) and provides reusable fixtures
for all test files.
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.main import app
from app.database import Base, get_db
from app.models import User
from app.auth import get_password_hash

# Load environment variables
load_dotenv()

# Use test database URL from env, or default to MySQL test database
# Format: mysql+pymysql://user:password@host:port/database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "mysql+pymysql://root:rootpassword@localhost:3306/emo_energy_test"
)

# Create test database engine (MySQL)
engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True to see SQL queries in test output
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    
    Steps:
    1. Create all tables (fresh start)
    2. Yield database session
    3. Rollback and drop tables after test
    
    This ensures each test starts with a clean database.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Cleanup: rollback any uncommitted changes
        db.rollback()
        db.close()
        # Drop all tables for clean state
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """
    Create FastAPI test client with test database.
    
    This fixture:
    1. Overrides get_db() to use test database session
    2. Provides TestClient for making HTTP requests
    3. Cleans up dependency overrides after test
    """
    def override_get_db():
        """Override get_db() to use test database session."""
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup: remove dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """
    Create a test user for authentication tests.
    
    This user is automatically created before each test that needs it.
    Username: testuser
    Password: testpassword123
    """
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

