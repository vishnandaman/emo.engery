"""
Content management router - handles content CRUD operations.

This module contains endpoints for:
- Creating content (with text analysis)
- Retrieving user's content list
- Retrieving specific content
- Deleting content
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Content
from app.schemas import ContentCreate, ContentResponse, ContentListResponse
from app.auth import get_current_user
from app.services.ai_service import analyze_text

# Create router for content endpoints
router = APIRouter()


async def process_content_ai(content_id: int, text: str):
    """
    Background task to process content.
    
    This function runs asynchronously after the content is created.
    It calls the analysis service to generate summary and sentiment,
    then updates the database record.
    
    Note: Creates its own database session since background tasks
    run after the request completes and the original session is closed.
    
    Args:
        content_id: ID of the content to process
        text: The text content to analyze
    """
    # Create a new database session for the background task
    # We can't reuse the request session as it will be closed
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        result = await analyze_text(text)
        
        print(f"Analysis result for content {content_id}: summary={result.get('summary')[:50] if result.get('summary') else 'None'}..., sentiment={result.get('sentiment')}")
        
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            summary_value = result.get("summary")
            sentiment_value = result.get("sentiment")
            
            print(f"Updating content {content_id}: summary='{summary_value}', sentiment={sentiment_value}")
            
            content.summary = summary_value
            content.sentiment = sentiment_value
            db.commit()
            
            print(f"Content {content_id} updated successfully")
        else:
            print(f"Content {content_id} not found in database")
    except Exception as e:
        print(f"Processing failed for content {content_id}: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()  # Rollback on error
        # Optionally, you could mark the content with an error status
    finally:
        db.close()  # Always close the session


@router.post("/contents", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new content and trigger analysis.
    
    This endpoint:
    1. Validates the input text
    2. Creates a new content record in the database
    3. Triggers background processing (non-blocking)
    4. Returns the content immediately (results will be added later)
    
    Args:
        content_data: ContentCreate schema with text field
        background_tasks: FastAPI background tasks for async processing
        current_user: Authenticated user (injected by get_current_user dependency)
        db: Database session
    
    Returns:
        ContentResponse: The created content object
    """
    # Validate text is not empty
    if not content_data.text or not content_data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty"
        )
    
    # Create new content object
    new_content = Content(
        user_id=current_user.id,
        text=content_data.text
    )
    
    # Save to database
    db.add(new_content)
    db.commit()
    db.refresh(new_content)  # Refresh to get auto-generated ID
    
    # Add background task for processing
    # This runs asynchronously and doesn't block the response
    # Note: We don't pass db session - the background task creates its own
    background_tasks.add_task(process_content_ai, new_content.id, content_data.text)
    
    return new_content


@router.get("/contents", response_model=ContentListResponse)
async def get_contents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all content for the authenticated user.
    
    This endpoint returns a paginated list of all content
    submitted by the current user.
    
    Args:
        current_user: Authenticated user
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        ContentListResponse: List of contents and total count
    """
    # Query contents for current user only
    contents = db.query(Content).filter(
        Content.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    # Get total count
    total = db.query(Content).filter(
        Content.user_id == current_user.id
    ).count()
    
    return {
        "contents": contents,
        "total": total
    }


@router.get("/contents/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific content by ID.
    
    This endpoint returns a single content item if it belongs to the user.
    
    Args:
        content_id: ID of the content to retrieve
        current_user: Authenticated user
        db: Database session
    
    Returns:
        ContentResponse: The content object with summary and sentiment
    
    Raises:
        HTTPException: If content not found or doesn't belong to user
    """
    # Find content by ID and user_id (security: users can only access their own content)
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return content


@router.delete("/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific content by ID.
    
    This endpoint permanently deletes content if it belongs to the user.
    
    Args:
        content_id: ID of the content to delete
        current_user: Authenticated user
        db: Database session
    
    Raises:
        HTTPException: If content not found or doesn't belong to user
    """
    # Find content by ID and user_id
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Delete from database
    db.delete(content)
    db.commit()
    
    # Return 204 No Content (successful deletion)
    return None

