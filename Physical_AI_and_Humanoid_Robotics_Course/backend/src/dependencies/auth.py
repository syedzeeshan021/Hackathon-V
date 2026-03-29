from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError
from pydantic import BaseModel
from datetime import datetime

# Assuming these are available from config and models
from backend.src.core.config import settings
from backend.src.models.user import UserInDB, UserBackground

# Placeholder for a function that fetches a user from the database
# In a real app, this would query your database
async def get_user_from_db(user_id: str) -> Optional[UserInDB]:
    # Simulate fetching a user
    if user_id == "test_user_id":
        return UserInDB(
            id=user_id,
            email="test@example.com",
            background=UserBackground.NONE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            password_hash="hashed_password_from_better_auth"
        )
    return None

async def get_current_user(authorization: Optional[str] = Header(None)) -> UserInDB:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        scheme, credentials = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        # In a real application, you would use Better-Auth's public key
        # to decode and verify the token. For now, this is a placeholder.
        # Ensure the algorithm matches what Better-Auth.com uses.
        payload = jwt.decode(
            credentials, 
            "your-better-auth-public-key-or-secret", # Replace with actual public key/secret
            algorithms=["HS256"], # Replace with actual algorithm from Better-Auth
            audience=settings.BETTER_AUTH_CLIENT_ID
        )
        user_id: str = payload.get("sub") # 'sub' is typically the user ID
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: User ID not found")
        
        user = await get_user_from_db(user_id) # Fetch user from your database
        if user is None:
            raise HTTPException(status_code=401, detail="User not found in database")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")