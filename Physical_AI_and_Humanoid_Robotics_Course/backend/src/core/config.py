from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Physical AI & Humanoid Robotics Textbook API"
    DATABASE_URL: str
    QDRANT_HOST: str
    QDRANT_API_KEY: str
    BETTER_AUTH_CLIENT_ID: str
    BETTER_AUTH_CLIENT_SECRET: str
    TRANSLATION_API_KEY: str = None # Optional, as per spec it's a bonus
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"] # Default for frontend

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()