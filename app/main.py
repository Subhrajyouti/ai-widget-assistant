import logging
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.api.chat import router as chat_router
from app.core.redis_client import redis_client
from app.core.config import settings


app = FastAPI(title="HappyFares Backend - Local", version="0.1.0")
app.include_router(chat_router, prefix="/api")


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])




@app.on_event("startup")
async def startup_event():
 logging.info("Starting up - connecting to Redis (or switching to in-memory fallback)")
 await redis_client.connect()
 logging.info("Startup completed")




@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Shutting down - closing Redis")
    await redis_client.close()




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)