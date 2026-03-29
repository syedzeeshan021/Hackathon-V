from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from backend.src.models.user import UserBackground, UserInDB
from backend.src.dependencies.auth import get_current_user # Assuming a dependency for current user

router = APIRouter()

class UserProfileUpdate(BaseModel):
    background: UserBackground

@router.post("/users/me/profile")
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: UserInDB = Depends(get_current_user) # Protect this endpoint
):
    # In a real application, you would update the user's background in the database
    # For now, we'll just simulate the update
    current_user.background = profile_update.background
    
    return {"message": "User profile updated successfully", "user": current_user}

@router.get("/users/me", response_model=UserInDB)
async def get_my_profile(
    current_user: UserInDB = Depends(get_current_user)
):
    # Return the current user's profile
    return current_user