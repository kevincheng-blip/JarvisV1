"""
J-GOD Feature Store v1

統一入口模組，提供標準化的因子/指標存取介面。

Feature Store 是 J-GOD 的「因子資產中樞」，所有 Prediction / Strategy / Path A
模組都應從這裡讀取因子，而非直接查詢資料庫。
"""

from jgod.feature_store.feature_store import (
    FeatureStore,
    FeatureSet,
    IndicatorInfo,
    FeatureStoreError,
    InsufficientCoverageError,
)

__all__ = [
    "FeatureStore",
    "FeatureSet",
    "IndicatorInfo",
    "FeatureStoreError",
    "InsufficientCoverageError",
]

