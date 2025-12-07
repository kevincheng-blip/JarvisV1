"""
J-GOD API Main Entry Point

FastAPI application for simulation data and predictions API.

Usage:
    uvicorn jgod.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jgod.api.routers import indicators, predictions, universe

app = FastAPI(
    title="J-GOD Simulation API",
    description="J-GOD Backfill & Simulation Data API (Simulation-Only)",
    version="1.0.0",
)

# CORS middleware (allow React UI to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(indicators.router, prefix="/api", tags=["indicators"])
app.include_router(universe.router, prefix="/api", tags=["universe"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "J-GOD Simulation API",
        "version": "1.0.0",
        "status": "Simulation-Only (DRY_RUN / PAPER modes only)",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

