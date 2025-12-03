"""
Database configuration and session management.

This module sets up SQLAlchemy for database operations.
SQLAlchemy is an ORM (Object-Relational Mapping) that allows us to
work with databases using Python objects instead of raw SQL.

Using MySQL database for production deployment.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root@localhost:3306/emo_energy")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI to get database session.
    
    This is a generator function that yields a database session.
    FastAPI will automatically close the session after the request completes.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the route handler
    finally:
        db.close()  # Always close the session, even if an error occurs

