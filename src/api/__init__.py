"""FastAPI application initialization."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from src.utils.logger import logger
from src.api.security import SecurityMiddleware

# Create FastAPI app
app = FastAPI(
    title=settings.agent_name,
    version=settings.agent_version,
    description=settings.agent_description
)

# Log startup
logger.info("Initializing retroBot API server...")
logger.info(f"Agent: {settings.agent_name} v{settings.agent_version}")
logger.info(f"Model: {settings.default_model}")
logger.info(f"Provider: {settings.llm_provider}")

# Security middleware (FIRST - most important!)
app.add_middleware(SecurityMiddleware)
logger.info("🔒 Security middleware enabled")

# CORS middleware (Warden Protocol compatible)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-pagination-total", "x-pagination-next", "content-location", "location"],
)

# Import and include routers
from src.api import langgraph_api, health, backward_compatible

app.include_router(langgraph_api.router, prefix="")
app.include_router(health.router, prefix="/health")
app.include_router(backward_compatible.router, prefix="")

@app.get("/")
@app.post("/")
async def root():
    """Root endpoint - LangGraph Cloud API compatible."""
    return {
        "name": settings.agent_name,
        "version": settings.agent_version,
        "status": "running",
        "description": settings.agent_description,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "info": "/info",
            "assistants": "/assistants",
            "threads": "/threads",
            "runs": "/runs/wait"
        }
    }


@app.get("/.well-known/agent-card.json")
async def agent_card():
    """Warden App agent discovery card."""
    return {
        "name": settings.agent_name,
        "version": settings.agent_version,
        "description": settings.agent_description,
        "capabilities": [
            "Real-time cryptocurrency prices from 3 exchanges",
            "Technical analysis (RSI, MA, MACD, Bollinger Bands)",
            "1000+ crypto tokens supported",
            "Conversation with context",
            "Multi-language support"
        ],
        "endpoints": {
            "base": "/",
            "assistants": "/assistants",
            "threads": "/threads",
            "runs": "/runs/wait",
            "stream": "/runs/stream"
        },
        "provider": "NeoNodes AI",
        "api_version": "1.0.0"
    }

@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    logger.info("✅ retroBot API server started successfully!")
    logger.info("📊 Health check at: /health")
    logger.info("📡 LangGraph API ready")
    logger.info("🚀 Warden App compatible")

@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    logger.info("🛑 retroBot API server shutting down...")

