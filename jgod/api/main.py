"""
J-GOD API Main Entry Point

FastAPI application for simulation data and predictions API.

Usage:
    uvicorn jgod.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jgod.api.routers import indicators, predictions, predictions_v2, universe, strategy, decision, decision_v3, policy, backtest, error_review, orders, error_replay, decision_ab, signal_conflict, doctrine_alert, self_repair, doctrine_v2, doctrine_patch, rule_sim, s_rank_engine, s_rank_v2, strategy_perf, observer, execution, intelligence

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
app.include_router(decision_v3.router, prefix="/api/v1/decision-v3", tags=["decision-v3"])
app.include_router(execution.router, prefix="/api/v1/execution", tags=["execution"])
app.include_router(policy.router, prefix="/api/v1/policy", tags=["policy"])
app.include_router(backtest.router)
app.include_router(error_review.router, prefix="/api/v1/error-review", tags=["error-review"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(error_replay.router, prefix="/api/v1/error-replay", tags=["error-replay"])
app.include_router(decision_ab.router, prefix="/api/v1", tags=["decision-ab"])
app.include_router(signal_conflict.router, prefix="/api/v1/predictions", tags=["signal-conflict"])
app.include_router(doctrine_alert.router, prefix="/api/v1/doctrine", tags=["doctrine-alert"])
app.include_router(self_repair.router, prefix="/api/v1/knowledge/self-repair", tags=["self-repair"])
app.include_router(doctrine_v2.router, prefix="/api/v2/doctrine", tags=["doctrine-v2"])
app.include_router(doctrine_patch.router, prefix="/api/v1/doctrine", tags=["doctrine-patch"])
app.include_router(rule_sim.router, prefix="/api/v1/rule-sim", tags=["rule-sim"])
app.include_router(s_rank_engine.router, prefix="/api/v1/s-rank", tags=["s-rank"])
app.include_router(s_rank_v2.router, prefix="/api/v1/s-rank-v2", tags=["s-rank-v2"])
app.include_router(strategy_perf.router, prefix="/api/v1/strategy-perf", tags=["strategy-perf"])
app.include_router(observer.router, prefix="/api/v1/observer", tags=["observer"])
app.include_router(intelligence.router)  # v0.6.13-P1.1: Intelligence status (already has /api/v1/intelligence prefix)

# v0.6.8-A8: Walk-Forward & Config routers
# v0.6.11-A11: Execution Engine router (already registered above at line 41)
from jgod.api.routers import walkforward, config
app.include_router(walkforward.router, prefix="/api/v1/walkforward", tags=["walkforward"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])

# v0.6.11-A11: Execution Engine router
from jgod.api.routers import execution as execution_router
app.include_router(execution_router.router)  # Already has /api/v1/execution prefix


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

