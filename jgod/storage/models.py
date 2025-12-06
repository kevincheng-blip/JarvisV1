"""
Database Models for J-GOD Simulation Data

ORM models for stocks, indicators, predictions, and virtual trades.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Stock(Base):
    """標的基本資訊表（stocks）"""
    
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, unique=True, index=True)
    name_zh = Column(String)
    name_en = Column(String)
    sector = Column(String)  # 產業分類（簡化版，可擴充為 sector_zh/sector_en）
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DailyBar(Base):
    """歷史日線資料表（daily_bars）"""
    
    __tablename__ = "daily_bars"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    turnover = Column(Float, nullable=True)  # 成交金額（可選）
    adjusted_close = Column(Float, nullable=True)  # 還原權值收盤價（可選）
    source = Column(String, default="FinMind")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_daily_bars_symbol_date"),
    )


class IndicatorSnapshot(Base):
    """100 指標快照表（indicator_snapshots）"""
    
    __tablename__ = "indicator_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False)
    indicator_code = Column(String, nullable=False)  # e.g. "P01", "C08", "F05", "M12"
    raw_value = Column(Float, nullable=True)
    normalized_value = Column(Float, nullable=True)  # -1.0 ~ +1.0
    weight = Column(Float, nullable=True)
    category = Column(String)  # "Price", "Capital", "Fundamental", "Catalyst", "Sentiment", "Quant", "X", "M"
    data_source = Column(String)  # 對應 FinMind 或其他來源
    status = Column(String, default="ok")  # "ok" / "missing" / "placeholder"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("symbol", "date", "indicator_code", name="uq_indicator_snapshot"),
    )


class PredictionSnapshot(Base):
    """選股結果快照表（prediction_snapshots）"""
    
    __tablename__ = "prediction_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    score = Column(Float, nullable=True)  # J-GOD 總分（與 total_score 相同，用於兼容）
    total_score = Column(Float, nullable=True)  # J-GOD 總分（保留向後兼容）
    signal = Column(String, nullable=True)  # 交易訊號（與 verdict 相同，用於兼容）
    verdict = Column(String, nullable=True)  # "STRONG_BUY" / "BUY" / "NEUTRAL" / "AVOID" / "SHORT"
    positive_factors_json = Column(JSON, nullable=True)  # Top positive 指標列表（新欄位）
    negative_factors_json = Column(JSON, nullable=True)  # Top negative 指標列表（新欄位）
    risk_flags_json = Column(JSON, nullable=True)  # 風險標記列表（新增）
    meta_json = Column(JSON, nullable=True)  # 原始 model 輸出的其他欄位（新欄位）
    # 向後兼容欄位（保留）
    positive_indicators = Column(JSON, nullable=True)  # Top positive 指標列表（向後兼容）
    negative_indicators = Column(JSON, nullable=True)  # Top negative 指標列表（向後兼容）
    raw_payload = Column(JSON, nullable=True)  # 完整 evaluate 結果（向後兼容）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_prediction_snapshot"),
    )


class VirtualTrade(Base):
    """模擬交易紀錄表（virtual_trades）"""
    
    __tablename__ = "virtual_trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    open_datetime = Column(DateTime, nullable=False)
    close_datetime = Column(DateTime, nullable=True)
    side = Column(String, nullable=False)  # "LONG" / "SHORT"
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    mode = Column(String, nullable=False)  # "DRY_RUN" / "PAPER" (LIVE is disabled)
    engine = Column(String)  # "PathE" / "PathD" / "ScenarioLab"
    strategy_tag = Column(String)  # e.g. "INTRADAY_ALPHA_V1"
    meta_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PortfolioSnapshot(Base):
    """組合淨值快照表（portfolio_snapshots）"""
    
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    snapshot_time = Column(DateTime(timezone=True), nullable=False, index=True)
    equity_curve = Column(Float)  # 資產淨值
    cash = Column(Float)
    positions_value = Column(Float)
    max_drawdown = Column(Float)
    sharpe = Column(Float, nullable=True)
    mode = Column(String, nullable=False)  # "DRY_RUN" / "PAPER"
    engine = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("snapshot_time", "mode", "engine", name="uq_portfolio_snapshot"),
    )

