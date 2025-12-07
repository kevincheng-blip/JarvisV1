"""
J-GOD Feature Store v1 - Core Implementation

提供標準化的因子/指標存取介面，從 indicator_snapshots 資料表讀取資料。
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from jgod.storage.db import get_session
from jgod.storage.models import IndicatorSnapshot


class FeatureStoreError(Exception):
    """Feature Store 基礎例外"""
    pass


class InsufficientCoverageError(FeatureStoreError):
    """指標覆蓋率不足例外（當 strict=True 且 coverage < min_indicator_count）"""
    pass


@dataclass
class IndicatorInfo:
    """單一指標資訊"""
    indicator_code: str
    category: str
    raw_value: Optional[float] = None
    normalized_value: Optional[float] = None
    weight: Optional[float] = None
    status: str = "OK"
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "indicator_code": self.indicator_code,
            "category": self.category,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "weight": self.weight,
            "status": self.status,
        }


@dataclass
class FeatureSet:
    """Feature Set：標準化的因子集合"""
    symbol: str
    date: date
    total_indicators: int  # 預期指標數（預設 100，但支援動態）
    available_indicators: int  # 實際可用指標數
    coverage_ratio: float  # available_indicators / total_indicators
    coverage_warning: bool = False  # 當 coverage < min_indicator_count 時
    indicators: List[IndicatorInfo] = field(default_factory=list)
    
    def to_dict(self, include_indicators: bool = True) -> Dict:
        """轉換為字典（API 回應格式）"""
        result = {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "total_indicators": self.total_indicators,
            "available_indicators": self.available_indicators,
            "coverage_ratio": round(self.coverage_ratio, 4),
            "coverage_warning": self.coverage_warning,
        }
        
        if include_indicators:
            result["indicators"] = [ind.to_dict() for ind in self.indicators]
        
        return result
    
    def to_feature_vector(self, use_normalized: bool = True, include_weights: bool = False) -> Dict[str, float]:
        """
        轉換為特徵向量（字典格式，key 為 indicator_code）
        
        Args:
            use_normalized: 使用 normalized_value（True）或 raw_value（False）
            include_weights: 是否將 weight 乘上 value
        
        Returns:
            Dict[str, float]: {indicator_code: value, ...}
        """
        vector = {}
        for ind in self.indicators:
            if ind.status != "OK":
                continue
            
            value = ind.normalized_value if use_normalized else ind.raw_value
            if value is None:
                continue
            
            if include_weights and ind.weight is not None:
                value = value * ind.weight
            
            vector[ind.indicator_code] = value
        
        return vector


class FeatureStore:
    """
    Feature Store：統一入口，提供標準化的因子存取介面
    
    設計原則：
    - 所有因子讀取都透過 Feature Store，避免各模組直接查詢 DB
    - 支援 coverage 檢查與警告機制
    - 回傳結構固定的 FeatureSet 物件
    """
    
    # 預設預期指標數（100 指標框架）
    DEFAULT_EXPECTED_INDICATORS = 100
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化 Feature Store
        
        Args:
            session: SQLAlchemy Session（如果為 None，則使用 get_session()）
        """
        self._session = session
        self._session_generator = None
    
    def _get_session(self) -> Session:
        """取得 Session（支援外部注入或自動生成）"""
        if self._session is not None:
            return self._session
        
        # 使用 generator 模式
        if self._session_generator is None:
            self._session_generator = get_session()
        return next(self._session_generator)
    
    def get_features(
        self,
        symbol: str,
        date: date,
        min_indicator_count: int = 90,
        strict: bool = False,
        expected_indicators: Optional[int] = None,
    ) -> Optional[FeatureSet]:
        """
        取得指定 symbol + date 的所有指標（標準化格式）
        
        Args:
            symbol: 股票代號
            date: 日期
            min_indicator_count: 最少需要的指標數量（預設 90）
            strict: 嚴格模式，若 coverage < min_indicator_count 則拋出例外
            expected_indicators: 預期指標數（預設 100，支援動態擴充）
        
        Returns:
            FeatureSet: 標準化的因子集合，如果 strict=False 且資料不足則回傳 None
        
        Raises:
            InsufficientCoverageError: 當 strict=True 且 coverage < min_indicator_count
            FeatureStoreError: 其他錯誤（例如 DB 連線失敗）
        """
        if expected_indicators is None:
            expected_indicators = self.DEFAULT_EXPECTED_INDICATORS
        
        # 查詢資料庫
        session = self._get_session()
        try:
            snapshots = (
                session.query(IndicatorSnapshot)
                .filter(
                    IndicatorSnapshot.symbol == symbol,
                    IndicatorSnapshot.date == date,
                )
                .order_by(IndicatorSnapshot.indicator_code)
                .all()
            )
        except Exception as e:
            raise FeatureStoreError(f"Failed to query indicator_snapshots: {e}") from e
        
        # 如果沒有資料，回傳 None
        if not snapshots:
            if strict:
                raise InsufficientCoverageError(
                    f"No indicators found for {symbol} on {date}"
                )
            return None
        
        # 組裝 IndicatorInfo 列表
        indicators = []
        for snap in snapshots:
            # 判斷 status
            status = snap.status or "OK"
            if status not in ["OK", "ok"]:
                # 如果 status 是 "missing" 或 "placeholder"，標記為 MISSING
                if status.lower() in ["missing", "placeholder"]:
                    status = "MISSING"
                elif status.lower() in ["bad", "bad_data", "error"]:
                    status = "BAD_DATA"
            
            # 檢查資料品質
            if status == "OK":
                # 如果 normalized_value 或 raw_value 都為 None，可能資料有問題
                if snap.normalized_value is None and snap.raw_value is None:
                    status = "BAD_DATA"
            
            indicator_info = IndicatorInfo(
                indicator_code=snap.indicator_code,
                category=snap.category or "UNKNOWN",
                raw_value=snap.raw_value,
                normalized_value=snap.normalized_value,
                weight=snap.weight,
                status=status,
            )
            indicators.append(indicator_info)
        
        # 計算 coverage
        available_indicators = len([ind for ind in indicators if ind.status == "OK"])
        coverage_ratio = available_indicators / expected_indicators if expected_indicators > 0 else 0.0
        coverage_warning = available_indicators < min_indicator_count
        
        # 嚴格模式檢查
        if strict and coverage_warning:
            raise InsufficientCoverageError(
                f"Insufficient coverage for {symbol} on {date}: "
                f"{available_indicators}/{expected_indicators} indicators available "
                f"(minimum required: {min_indicator_count})"
            )
        
        # 組裝 FeatureSet
        feature_set = FeatureSet(
            symbol=symbol,
            date=date,
            total_indicators=expected_indicators,
            available_indicators=available_indicators,
            coverage_ratio=coverage_ratio,
            coverage_warning=coverage_warning,
            indicators=indicators,
        )
        
        return feature_set
    
    def get_feature_vector(
        self,
        symbol: str,
        date: date,
        normalize: bool = True,
        include_weights: bool = False,
        min_indicator_count: int = 90,
        strict: bool = False,
    ) -> Optional[Dict[str, float]]:
        """
        取得特徵向量（字典格式，key 為 indicator_code）
        
        這是一個便利方法，直接回傳字典格式的特徵向量，適合用於機器學習/策略模型。
        
        Args:
            symbol: 股票代號
            date: 日期
            normalize: 使用 normalized_value（True）或 raw_value（False）
            include_weights: 是否將 weight 乘上 value
            min_indicator_count: 最少需要的指標數量
            strict: 嚴格模式
        
        Returns:
            Dict[str, float]: {indicator_code: value, ...}，如果 strict=False 且資料不足則回傳 None
        """
        feature_set = self.get_features(
            symbol=symbol,
            date=date,
            min_indicator_count=min_indicator_count,
            strict=strict,
        )
        
        if feature_set is None:
            return None
        
        return feature_set.to_feature_vector(
            use_normalized=normalize,
            include_weights=include_weights,
        )

