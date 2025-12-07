"""
Indicators API Router

Endpoints for 100-indicator snapshots.

此 API 已被重構為使用 Feature Store v1，提供標準化的因子存取介面。
"""

from datetime import date, datetime
from typing import List

from fastapi import APIRouter, HTTPException

from jgod.feature_store import FeatureStore, FeatureStoreError, InsufficientCoverageError

router = APIRouter()

# Feature Store 實例（單例模式，共享 Session）
_feature_store = FeatureStore()


@router.get("/indicators/{symbol}/{date}")
async def get_indicators_by_symbol_date(
    symbol: str,
    date: str,
):
    """
    Get 100-indicator snapshot for a symbol on a specific date.
    
    **用途**：主要給前端 UI（Indicator Radar/Heatmap）使用，回傳格式保持向後兼容。
    
    **底層實作**：已改為使用 Feature Store v1，提供標準化的因子存取。
    
    Returns:
        - symbol
        - date
        - indicators: list of indicator objects (保持原有格式，向後兼容)
        - total_indicators: 預期指標數（新增）
        - available_indicators: 實際可用指標數（新增）
        - coverage_ratio: 覆蓋率（新增）
    """
    try:
        as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Use YYYY-MM-DD")
    
    try:
        # 使用 Feature Store 取得資料（非嚴格模式，允許 coverage 不足）
        feature_set = _feature_store.get_features(
            symbol=symbol,
            date=as_of_date,
            min_indicator_count=90,
            strict=False,
        )
        
        if feature_set is None:
            raise HTTPException(
                status_code=404,
                detail=f"Indicators not found for {symbol} on {date}",
            )
        
        # 轉換為向後兼容格式（保持原有 API 回應結構）
        indicators = [ind.to_dict() for ind in feature_set.indicators]
        
        # 回傳格式：保持原有欄位，新增 coverage 相關資訊
        return {
            "symbol": symbol,
            "date": date,
            "indicators": indicators,
            # 新增欄位（向後兼容）
            "total_indicators": feature_set.total_indicators,
            "available_indicators": feature_set.available_indicators,
            "coverage_ratio": round(feature_set.coverage_ratio, 4),
            "coverage_warning": feature_set.coverage_warning,
        }
        
    except InsufficientCoverageError as e:
        # 理論上不會發生（strict=False），但為了完整性還是處理
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except FeatureStoreError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feature Store error: {str(e)}",
        )


@router.get("/v1/features/{symbol}/{date}")
async def get_features_v1(
    symbol: str,
    date: str,
    min_indicator_count: int = 90,
    strict: bool = False,
):
    """
    Get features for a symbol on a specific date (v1 API - 面向機器/策略使用).
    
    **用途**：專門給策略引擎、回測系統、AI 模型使用，回傳更完整的 metadata。
    
    **與 /indicators/{symbol}/{date} 的差別**：
    - `/indicators/{symbol}/{date}`：面向前端 UI，格式向後兼容，允許 coverage 不足
    - `/v1/features/{symbol}/{date}`：面向機器/策略，提供完整 metadata，支援嚴格模式
    
    **參數**：
    - min_indicator_count: 最少需要的指標數量（預設 90）
    - strict: 嚴格模式，若 coverage < min_indicator_count 則回傳 404
    
    Returns:
        - symbol
        - date
        - total_indicators: 預期指標數
        - available_indicators: 實際可用指標數
        - coverage_ratio: 覆蓋率
        - coverage_warning: 是否低於最低門檻
        - indicators: 完整指標列表（包含 status）
    """
    try:
        as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Use YYYY-MM-DD")
    
    try:
        # 使用 Feature Store 取得資料
        feature_set = _feature_store.get_features(
            symbol=symbol,
            date=as_of_date,
            min_indicator_count=min_indicator_count,
            strict=strict,
        )
        
        if feature_set is None:
            raise HTTPException(
                status_code=404,
                detail=f"Features not found for {symbol} on {date}",
            )
        
        # 回傳完整的 FeatureSet 格式（面向機器使用）
        return feature_set.to_dict(include_indicators=True)
        
    except InsufficientCoverageError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except FeatureStoreError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feature Store error: {str(e)}",
        )

