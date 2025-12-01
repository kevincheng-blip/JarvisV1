"""Optimizer Constraints Builder

將 OptimizerConfig + 輸入資料（如 factor_exposure, sector_map）
轉成 OptimizerCore 可以直接使用的 numpy 結構。

Reference: docs/J-GOD_OPTIMIZER_STANDARD_v1.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .optimizer_config import OptimizerConfig


class ConstraintBuilder:
    """
    專責將 OptimizerConfig + 輸入資料（如 factor_exposure, sector_map）
    轉成 OptimizerCore 可以直接使用的 numpy 結構。
    """

    def __init__(self, config: OptimizerConfig) -> None:
        """Initialize ConstraintBuilder with OptimizerConfig

        Args:
            config: OptimizerConfig instance
        """
        self.config = config

    def build_weight_bounds(
        self,
        stock_ids: List[str],
    ) -> List[Tuple[float, float]]:
        """
        根據 WeightConstraints 產生 (min, max) bound list。

        v1 版本：所有股票共用同一組 min/max。

        Args:
            stock_ids: List of stock identifiers

        Returns:
            List of (min_weight, max_weight) tuples for each stock
        """
        weight_config = self.config.weight_constraints
        
        min_weight = weight_config.min_weight
        max_weight = weight_config.max_weight
        
        # 如果是 long_only，min_weight 至少為 0
        if weight_config.long_only:
            min_weight = max(min_weight, 0.0)
        
        # 產生每個股票的 bounds（v1 版本：全部相同）
        bounds = [(min_weight, max_weight) for _ in stock_ids]
        
        return bounds

    def build_factor_exposure_constraints(
        self,
        factor_exposure: pd.DataFrame,
    ) -> Dict[str, Tuple[float, float]]:
        """
        將因子暴露限制轉成 {factor_name: (min, max)}。

        如果 config.factor_constraints.factor_bounds 為空，則回傳空 dict。

        Args:
            factor_exposure: DataFrame with index=stock_id, columns=factor_names

        Returns:
            Dictionary mapping factor names to (min_exposure, max_exposure) bounds
        """
        factor_bounds = self.config.factor_constraints.factor_bounds
        
        if not factor_bounds:
            return {}
        
        # 驗證因子名稱是否存在於 factor_exposure 的 columns
        valid_bounds = {}
        for factor_name, (min_val, max_val) in factor_bounds.items():
            if factor_name in factor_exposure.columns:
                valid_bounds[factor_name] = (min_val, max_val)
            # 如果因子不存在，略過（可以選擇記錄警告）
        
        return valid_bounds

    def build_sector_constraints(
        self,
        stock_ids: List[str],
        sector_map: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict]:
        """
        產生 sector 中性的矩陣 / 權重限制表示法。

        v1 版本：
        - 若 sector_constraints.enabled=False 或 sector_map 為 None，則回傳 None。
        - 否則回傳結構:
            {
                'sectors': List[str],
                'exposure_matrix': np.ndarray (len(sectors) x len(stock_ids)),
                'bounds': Dict[sector, (min_delta, max_delta)]
            }

        Args:
            stock_ids: List of stock identifiers
            sector_map: Optional dictionary mapping stock_id -> sector_name

        Returns:
            Dictionary with sector constraint structure, or None if disabled
        """
        if not self.config.sector_constraints.enabled:
            return None
        
        if sector_map is None:
            return None
        
        # 取得所有唯一的 sectors
        sectors = sorted(set(sector_map.values()))
        
        if not sectors:
            return None
        
        # 建立 exposure matrix: (num_sectors x num_stocks)
        num_sectors = len(sectors)
        num_stocks = len(stock_ids)
        
        exposure_matrix = np.zeros((num_sectors, num_stocks))
        
        for i, stock_id in enumerate(stock_ids):
            sector = sector_map.get(stock_id)
            if sector in sectors:
                sector_idx = sectors.index(sector)
                exposure_matrix[sector_idx, i] = 1.0
        
        # 取得各 sector 的 bounds（若未設定，預設為無限制）
        bounds = {}
        sector_bounds_config = self.config.sector_constraints.sector_bounds
        
        for sector in sectors:
            if sector in sector_bounds_config:
                bounds[sector] = sector_bounds_config[sector]
            else:
                # 若未設定，預設為無限制（使用很大的數值）
                bounds[sector] = (-np.inf, np.inf)
        
        return {
            'sectors': sectors,
            'exposure_matrix': exposure_matrix,
            'bounds': bounds,
        }

