import logging
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.core.redis_client import redis_client
from app.core.config import settings

# ------------------------------------------------------------
# FastAPI App Initialization
# ------------------------------------------------------------
app = FastAPI(
    title="HappyFares AI Backend (Local)",
    version="0.2.0",
    description="Backend API for AI Flight Assistant extension."
)

# Include the main router
app.include_router(chat_router, prefix="/api")

# ------------------------------------------------------------
# CORS Configuration
# ------------------------------------------------------------
# You can restrict origins later to your deployed domain or Chrome extension ID
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # For development; restrict later to ["chrome-extension://<your-id>"]
        "http://127.0.0.1",
        "http://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Startup & Shutdown Events
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logging.info("🚀 Starting up - Initializing Redis connection...")
    try:
        pong = await redis_client.ping()
        if pong:
            logging.info("✅ Redis connected successfully.")
        else:
            logging.warning("⚠️ Redis ping failed. Using fallback (if configured).")
    except Exception as e:
        logging.error(f"❌ Redis connection error: {e}")
    logging.info("Startup completed.")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("🔻 Shutting down - closing Redis connection.")
    try:
        await redis_client.close()
        logging.info("✅ Redis connection closed cleanly.")
    except Exception as e:
        logging.error(f"Error closing Redis: {e}")

# ------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(getattr(settings, "APP_PORT", 8000)),
        reload=True,
        log_level="info"
    )
