"""Health check endpoints."""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check."""
    return {
        "ready": True,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/live")
async def liveness_check():
    """Liveness check."""
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat()
    }

