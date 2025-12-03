"""
Authentication utilities for JWT token handling and password hashing.

This module provides functions for:
- Creating and verifying JWT tokens
- Hashing and verifying passwords
- Getting current authenticated user
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import hashlib
from dotenv import load_dotenv

from app.database import get_db
from app.models import User

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# HTTPBearer scheme for token extraction
# This shows a simple "Value" field in Swagger UI for Bearer tokens
# HTTPBearer automatically extracts the token from Authorization: Bearer <token> header
security = HTTPBearer()


def _prepare_password(password: str) -> bytes:
    """
    Prepare password for bcrypt hashing.
    
    Bcrypt has a 72-byte limit. For longer passwords, we pre-hash with SHA256
    to ensure consistent handling while maintaining security.
    
    Args:
        password: Plain text password
    
    Returns:
        bytes: Password ready for bcrypt (max 72 bytes)
    """
    # Convert to bytes to check length
    password_bytes = password.encode('utf-8')
    
    # If password is longer than 72 bytes, pre-hash with SHA256
    # SHA256 produces 32 bytes (256 bits), which is always under 72 bytes
    if len(password_bytes) > 72:
        # Pre-hash with SHA256 to get fixed-length hash (32 bytes)
        sha256_hash_bytes = hashlib.sha256(password_bytes).digest()
        return sha256_hash_bytes
    else:
        # Password is short enough, use as-is (but ensure it's bytes)
        return password_bytes


def _prepare_password_for_bcrypt(password: str) -> str:
    """
    Prepare password for bcrypt hashing.
    
    Bcrypt has a strict 72-byte limit. This function ensures the password
    is always within that limit by:
    1. If password <= 72 bytes: use as-is
    2. If password > 72 bytes: pre-hash with SHA256 (produces 64-byte hex string)
    
    Args:
        password: Plain text password
    
    Returns:
        str: Password ready for bcrypt (always <= 72 bytes when encoded)
    """
    password_bytes = password.encode('utf-8')
    
    # If password exceeds 72 bytes, pre-hash with SHA256
    if len(password_bytes) > 72:
        # SHA256 produces 32 bytes, hex representation is 64 characters
        # When encoded to UTF-8, 64 hex chars = 64 bytes (well under 72 limit)
        sha256_hash = hashlib.sha256(password_bytes).hexdigest()
        return sha256_hash
    
    # Password is within limit, use as-is
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    This function handles passwords of any length by using the same
    preparation method used during hashing.
    
    Args:
        plain_password: The password entered by user
        hashed_password: The stored password hash (bcrypt hash)
    
    Returns:
        bool: True if password matches, False otherwise
    """
    # Prepare password the same way it was hashed
    prepared_password = _prepare_password_for_bcrypt(plain_password)
    
    # Convert to bytes for bcrypt
    password_bytes = prepared_password.encode('utf-8')
    
    # Ensure it's within 72-byte limit
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Verify with bcrypt
    # hashed_password is already a bytes string from bcrypt
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Bcrypt has a 72-byte limit. This function ensures passwords of any
    length are handled correctly by pre-hashing long passwords with SHA256.
    
    Args:
        password: Plain text password
    
    Returns:
        str: Hashed password string (bcrypt hash, UTF-8 encoded)
    """
    # Prepare password to ensure it's within bcrypt's 72-byte limit
    prepared_password = _prepare_password_for_bcrypt(password)
    
    # Convert to bytes
    password_bytes = prepared_password.encode('utf-8')
    
    # Ensure it's within 72-byte limit (safety check)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash with bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string (bcrypt hash is bytes, decode to string for storage)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing user data (usually user ID or username)
        expires_delta: Optional custom expiration time
    
    Returns:
        str: Encoded JWT token string
    """
    to_encode = data.copy()  # Copy to avoid modifying original data
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration to token data
    to_encode.update({"exp": expire})
    
    # Encode and return JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency function to get current authenticated user from JWT token.
    
    This function is used as a dependency in protected routes.
    FastAPI will automatically call this and inject the User object.
    
    Args:
        credentials: HTTPBearer credentials containing the token
        db: Database session
    
    Returns:
        User: The authenticated user object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Decode and verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # "sub" (subject) contains username
        
        if username is None:
            raise credentials_exception
    except JWTError:
        # Token is invalid or expired
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

