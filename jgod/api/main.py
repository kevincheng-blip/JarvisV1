"""
J-GOD API Main Entry Point

FastAPI application for simulation data and predictions API.

Usage:
    uvicorn jgod.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jgod.api.routers import indicators, predictions, predictions_v2, universe, strategy, decision, policy, backtest, error_review, orders, error_replay, decision_ab, signal_conflict, doctrine_alert, self_repair, doctrine_v2, rule_sim, s_rank_engine

app = FastAPI(
    title="J-GOD Simulation API",
    description="J-GOD Backfill & Simulation Data API (Simulation-Only)",
    version="1.0.0",
)

# CORS middleware (allow React UI to connect)
# Only allow localhost origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(indicators.router, prefix="/api", tags=["indicators"])
app.include_router(universe.router, prefix="/api", tags=["universe"])
app.include_router(strategy.router, prefix="/api", tags=["strategy"])
app.include_router(decision.router, prefix="/api", tags=["decision"])
app.include_router(policy.router, prefix="/api/v1/policy", tags=["policy"])
app.include_router(backtest.router)
app.include_router(error_review.router, prefix="/api/v1/error-review", tags=["error-review"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(error_replay.router, prefix="/api/v1/error-replay", tags=["error-replay"])
app.include_router(decision_ab.router, prefix="/api/v1/decision/ab-report", tags=["decision-ab"])
app.include_router(signal_conflict.router, prefix="/api/v1/predictions", tags=["signal-conflict"])
app.include_router(doctrine_alert.router, prefix="/api/v1/doctrine", tags=["doctrine-alert"])
app.include_router(self_repair.router, prefix="/api/v1/knowledge/self-repair", tags=["self-repair"])
app.include_router(doctrine_v2.router, prefix="/api/v2/doctrine", tags=["doctrine-v2"])
app.include_router(rule_sim.router, prefix="/api/v1/rule-sim", tags=["rule-sim"])
app.include_router(s_rank_engine.router, prefix="/api/v1/s-rank", tags=["s-rank"])


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

