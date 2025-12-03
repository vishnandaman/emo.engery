"""
Authentication router - handles user registration and login.

This module contains endpoints for:
- User signup (registration)
- User login (authentication and token generation)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from app.database import get_db
from app.models import User
from app.schemas import UserSignup, UserLogin, Token
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create router for authentication endpoints
router = APIRouter()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    This endpoint:
    1. Validates input data (username, email, password)
    2. Hashes the password (never store plain passwords!)
    3. Creates a new user in the database
    4. Returns a JWT token for immediate authentication
    
    Args:
        user_data: UserSignup schema containing username, email, password
        db: Database session (injected by FastAPI)
    
    Returns:
        Token: JWT access token and token type
    
    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user object
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    # Save to database
    try:
        db.add(new_user)
        db.commit()  # Commit transaction
        db.refresh(new_user)  # Refresh to get auto-generated ID
    except IntegrityError:
        # Handle race condition (if user was created between checks)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create access token for the new user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username},  # "sub" = subject (username)
        expires_delta=access_token_expires
    )
    
    # Return token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    This endpoint:
    1. Finds user by username
    2. Verifies password
    3. Returns JWT token if credentials are valid
    
    Args:
        user_credentials: UserLogin schema with username and password
        db: Database session
    
    Returns:
        Token: JWT access token and token type
    
    Raises:
        HTTPException: If username or password is incorrect
    """
    # Find user by username
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

