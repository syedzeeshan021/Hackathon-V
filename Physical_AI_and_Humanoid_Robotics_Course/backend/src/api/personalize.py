from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from backend.src.dependencies.auth import get_current_user
from backend.src.models.user import UserInDB, UserBackground

router = APIRouter()

class PersonalizeRequest(BaseModel):
    chapter_id: str

class PersonalizeResponse(BaseModel):
    personalized_content: str
    original_chapter_id: str
    user_background: UserBackground
    message: str = "Content personalized based on user background (placeholder)."

@router.post("/personalize", response_model=PersonalizeResponse)
async def personalize_chapter_content(
    request: PersonalizeRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    # In a real application:
    # 1. Fetch the original chapter content based on request.chapter_id
    # 2. Apply personalization rules based on current_user.background
    #    (e.g., replace/insert code examples or hardware diagrams)
    # 3. This would likely involve a more sophisticated logic, potentially
    #    using another LLM call with context from PersonalizationRule data model.

    personalized_content = f"This is the personalized content for chapter '{request.chapter_id}'.\n"
    
    if current_user.background == UserBackground.SOFTWARE:
        personalized_content += "Here's a software-focused example: `print('Hello World')`\n"
    elif current_user.background == UserBackground.HARDWARE:
        personalized_content += "Here's a hardware-focused example: Connecting a resistor to an LED.\n"
    elif current_user.background == UserBackground.BOTH:
        personalized_content += "Here's a combined example: `robot.move(10)` connecting to motor driver.\n"
    else:
        personalized_content += "No specific personalization applied due to unknown background.\n"
    
    personalized_content += f"User background: {current_user.background}"

    return PersonalizeResponse(
        personalized_content=personalized_content,
        original_chapter_id=request.chapter_id,
        user_background=current_user.background
    )