from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from backend.src.core.config import settings
from backend.src.api import chat
from backend.src.api import users
from backend.src.api import personalize
from backend.src.api import translate # Import the translate router

app = FastAPI()

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Base API Router ---
api_router = APIRouter()

@api_router.get("/")
async def api_root():
    return {"message": "Welcome to the API router!"}

# Include other routers
api_router.include_router(chat.router, prefix="/chat", tags=["Chatbot"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(personalize.router, prefix="/personalize", tags=["Personalization"])
api_router.include_router(translate.router, prefix="/translate", tags=["Translation"]) # Include translate router

# Include this router in the main application
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI backend! Access API at /api"}