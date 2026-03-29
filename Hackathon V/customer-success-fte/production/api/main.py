# Customer Success FTE - FastAPI Application
# Main API entry point with all channel endpoints

import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import os
import sys

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from production.core.config import settings
from production.db import init_pool, close_pool, health_check as db_health_check
from production.channels import GmailHandler, WhatsAppHandler, WebFormHandler
from production.channels.web_form_handler import WebFormSubmitRequest, WebFormSubmitResponse, WebFormStatusResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Customer Success FTE API...")
    await init_pool()
    logger.info("Database connection pool initialized")

    yield

    # Shutdown
    logger.info("Shutting down Customer Success FTE API...")
    await close_pool()
    logger.info("Database connection pool closed")

# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered customer support across Gmail, WhatsApp, and Web Form",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# CHANNEL HANDLERS
# =============================================================================

# Initialize channel handlers
gmail_handler: Optional[GmailHandler] = None
whatsapp_handler: Optional[WhatsAppHandler] = None
web_form_handler: Optional[WebFormHandler] = None


@app.on_event("startup")
async def startup_handlers():
    """Initialize channel handlers."""
    global gmail_handler, whatsapp_handler, web_form_handler

    # Gmail handler (requires OAuth setup)
    gmail_handler = GmailHandler()
    logger.info("Gmail handler initialized")

    # WhatsApp handler (requires Twilio credentials)
    whatsapp_handler = WhatsAppHandler(
        account_sid=settings.twilio_account_sid,
        auth_token=settings.twilio_auth_token,
        from_number=settings.twilio_whatsapp_number
    )
    logger.info("WhatsApp handler initialized")

    # Web form handler
    web_form_handler = WebFormHandler()
    logger.info("Web form handler initialized")

# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "channels": {
            "gmail": settings.gmail_enabled,
            "whatsapp": settings.whatsapp_enabled,
            "web_form": settings.web_form_enabled
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    db_status = await db_health_check()

    channel_status = {}
    if gmail_handler:
        channel_status['gmail'] = await gmail_handler.health_check()
    if whatsapp_handler:
        channel_status['whatsapp'] = await whatsapp_handler.health_check()
    if web_form_handler:
        channel_status['web_form'] = await web_form_handler.health_check()

    overall_healthy = (
        db_status.get('status') == 'healthy' and
        all(c.get('status') in ['healthy', 'disabled'] for c in channel_status.values())
    )

    status_code = 200 if overall_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": db_status,
            "channels": channel_status
        }
    )

# =============================================================================
# GMAIL WEBHOOK ENDPOINTS
# =============================================================================

@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request):
    """
    Gmail Pub/Sub webhook endpoint.

    Receives notifications about new emails.
    """
    if not settings.gmail_enabled:
        raise HTTPException(status_code=400, detail="Gmail channel disabled")

    try:
        body = await request.json()
        logger.debug(f"Gmail webhook received: {body}")

        # Process the email asynchronously
        if gmail_handler:
            result = await gmail_handler.handle_pubsub_webhook(body)
            return result

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/gmail/callback")
async def gmail_oauth_callback(request: Request):
    """Gmail OAuth2 callback endpoint."""
    return {"status": "oauth_callback_received"}

# =============================================================================
# WHATSAPP WEBHOOK ENDPOINTS
# =============================================================================

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp webhook endpoint.

    Receives inbound WhatsApp messages.
    """
    if not settings.whatsapp_enabled:
        raise HTTPException(status_code=400, detail="WhatsApp channel disabled")

    try:
        form_data = await request.form()
        webhook_data = dict(form_data)

        logger.debug(f"WhatsApp webhook received from: {webhook_data.get('From', 'unknown')}")

        if whatsapp_handler:
            result = await whatsapp_handler.process_inbound_message(webhook_data)
            return result

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/webhooks/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """WhatsApp webhook verification (for testing)."""
    return {"status": "verified"}

# =============================================================================
# WEB FORM ENDPOINTS
# =============================================================================

@app.post("/webhooks/web-form", response_model=WebFormSubmitResponse)
async def web_form_submit(
    form_data: WebFormSubmitRequest,
    background_tasks: BackgroundTasks
):
    """
    Web form submission endpoint.

    Accepts support requests from the web form.
    """
    if not settings.web_form_enabled:
        raise HTTPException(status_code=400, detail="Web form channel disabled")

    try:
        if web_form_handler:
            response = await web_form_handler.process_form_submission(form_data)
            return response

        raise HTTPException(status_code=500, detail="Web form handler not initialized")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Web form error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets/{ticket_id}/status", response_model=WebFormStatusResponse)
async def get_ticket_status(ticket_id: str):
    """Get ticket status by ID."""
    try:
        if web_form_handler:
            status = await web_form_handler.get_ticket_status(ticket_id)
            return status

        raise HTTPException(status_code=500, detail="Handler not initialized")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ticket status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/instant")
async def instant_chat(
    email: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Instant chat endpoint for real-time support."""
    try:
        if web_form_handler:
            result = await web_form_handler.process_instant_message(
                email=email,
                message=message,
                session_id=session_id
            )
            return result

        raise HTTPException(status_code=500, detail="Handler not initialized")

    except Exception as e:
        logger.error(f"Instant chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# METRICS ENDPOINTS
# =============================================================================

@app.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    return {
        "timestamp": "2026-03-28T00:00:00Z",
        "channels": {
            "gmail": {"enabled": settings.gmail_enabled},
            "whatsapp": {"enabled": settings.whatsapp_enabled},
            "web_form": {"enabled": settings.web_form_enabled}
        },
        "database": await db_health_check()
    }

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "production.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
