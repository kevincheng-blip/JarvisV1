# 創世紀量化系統《15 Step Master Roadmap》v1

> **生成時間**：2024年11月28日  
> **生成依據**：11 本 AI 知識庫版完整內容  
> **身份**：Chief Engineer（首席工程師）

---

## 📋 Roadmap 總覽

本 Roadmap 涵蓋四大核心模組：
- **Data Layer**：API、Tick 處理、回放、資料庫
- **Factor Engine**：F_PT、F_MRR、F_Inertia、Orderbook、Alpha Engine
- **Model / RL Layer**：Transformer Agent、State Vector、Reward、Action
- **Execution / Risk Layer**：OrderRouter、TCA、F_Internal、Paper Trading

---

## 🗺️ 15 步工程 Roadmap

| Step No. | 步驟名稱 | 主要任務（工程細節） | 核心依賴（文件/數據源） |
|----------|----------|---------------------|----------------------|
| 1 | 數據管道與校準 | 建立 `data_pipeline/` 模組：<br>- `api_connectors/`：永豐 API、XQ 智富 API、Polygon.io、FinMind、期交所 API<br>- `tick_normalizer.py`：Tick 數據標準化、時間戳校準（NTP 同步）<br>- `data_validator.py`：數據完整性檢查、異常值過濾<br>- `storage_manager.py`：Parquet/HDF5 格式儲存、歷史數據回溯<br>- 建立 `DailyPrice` ORM 模型、三層 Schema 架構（原始數據/計算因子/模型結果） | `JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1.md`<br>`股市聖經四_AI知識庫版_v1.md`<br>永豐 API、XQ API、Polygon.io、FinMind |
| 2 | 信息時間引擎實施 | 建立 `strategy_engine/factor_FX_infotime.py`：<br>- `InfoTimeEngine` 類別：Volume Bar 生成器（K_VOLUME_BAR_SIZE = 5M）<br>- `process_tick()`：累積 Volume，形成 Volume Bar<br>- `calculate_infotime_factor()`：F_InfoTime = current_interval / long_term_avg_freq<br>- 事件序列基礎的 EMA 更新機制<br>- 測試檔：`tests/strategy_engine/test_factor_FX_infotime.py` | `股市大自然萬物修復法則_AI知識庫版_v1.md`<br>`雙引擎與自主演化閉環_AI知識庫版_v1.md`<br>Tick Data（永豐 API） |
| 3 | 微觀因子硬體加速 | 建立 `strategy_engine/factor_FX_microstructure.py`：<br>- `MicrostructureEngine`：VWAP 偏離、異常量能、攻擊型委託、委託簿壓力、價差變化<br>- `OrderbookAnalyzer`：五檔買賣壓比率（WOB Ratio）、訂單簿斜率計算<br>- 向量化計算（NumPy/Pandas）優化<br>- 異步處理架構（AsyncIO）整合 | `股市聖經三_AI知識庫版_v1.md`<br>`股神腦系統具體化設計_AI知識庫版_v1.md`<br>永豐 API（五檔報價）、XQ API（逐筆數據） |
| 4 | 資金流基礎引擎（SAI & MOI） | 建立 `strategy_engine/factor_FX_capital_flow.py`：<br>- `CapitalFlowEngine` 類別：核心計算引擎<br>- `calculate_capital_flow_factors(xq_data, current_market_volume)`：主計算接口<br>- `_calculate_sai_residual(group, current_share, mean_share, std_share)`：族群攻擊因子計算<br>- `_calculate_moi(major_buy_volume, major_sell_volume, total_major_volume)`：主力單量失衡計算<br>- `historical_group_weights`：pd.Series 格式的歷史參數管理（族群名稱 → 平均成交量占比）<br>- `default_std`：預設標準差參數（0.02）<br>- 輸出格式：`{"Group_SAI_Factors": {"SAI_Residual_AI_Concept": float, ...}, "MOI": float}`<br>- 測試檔：`tests/strategy_engine/test_factor_FX_capital_flow.py`（需測試 SAI 計算、MOI 計算、異常值處理） | `股神腦系統具體化設計_AI知識庫版_v1.md`<br>XQ API（族群資金流、主力大單數據）<br>Step 1（數據管道） |
| 5 | 流動性壁壘感知（F_Orderbook） | 建立 `strategy_engine/factor_FX_orderbook.py`：<br>- `OrderbookFactorEngine` 類別：訂單簿因子計算<br>- `compute_orderbook_slope(bid_prices, bid_volumes, ask_prices, ask_volumes)`：買賣盤斜率計算（五檔深度）<br>- `compute_aggregate_depth(bid_volumes, ask_volumes, depth_levels=5)`：聚合深度計算<br>- `IcebergFactorEngine` 類別：隱藏流動性預測<br>- `detect_iceberg_order(orderbook_snapshot, historical_patterns)`：Iceberg Order 偵測邏輯<br>- `calculate_orderbook_imbalance(bid_depth, ask_depth)`：委託簿失衡比率<br>- 輸出格式：`{"F_Orderbook_Slope": float, "F_Orderbook_Depth": float, "F_Orderbook_Imbalance": float, "F_Iceberg_Probability": float}`<br>- 測試檔：`tests/strategy_engine/test_factor_FX_orderbook.py`（需測試斜率計算、深度聚合、Iceberg 偵測） | `股市大自然萬物修復法則_AI知識庫版_v1.md`<br>永豐 API（完整訂單簿深度、五檔報價）<br>Step 1（數據管道） |
| 6 | 跨資產聯動因子（F_CrossAsset） | 建立 `strategy_engine/factor_FXA_crossasset.py`：<br>- `CrossAssetFactorEngine` 類別：跨資產因子計算<br>- `_calculate_cointegration_residual(local_price, adr_price, lookback_window=60)`：ADR Residual 計算（OLS 迴歸：`ln(Price_Local) = β * ln(Price_ADR) + α + residual`）<br>- `_calculate_inter_future_residual(tw_future, us_future, lookback_window=60)`：Inter-Future Residual 計算（`ln(IndexFutures_TW) = γ * ln(IndexFutures_US) + δ + residual`）<br>- `run_fxa_pipeline(symbol, adr_symbol, tw_future_symbol, us_future_symbol)`：完整跨資產因子管道<br>- `_standardize_to_zscore(residual, mean, std)`：Z-score 標準化<br>- 輸出格式：`{"F_CrossAsset_ADR_Residual": float, "F_CrossAsset_InterFuture_Residual": float, "F_CrossAsset_ADR_Zscore": float, "F_CrossAsset_InterFuture_Zscore": float}`<br>- 測試檔：`tests/strategy_engine/test_factor_FXA_crossasset.py`（需測試 Cointegration 分析、Z-score 標準化） | `股市聖經四_AI知識庫版_v1.md`<br>Polygon.io（ADR 價格）、期交所 API（期貨數據）<br>Step 1（數據管道） |
| 7 | 資金流慣性因子（F_Inertia） | 建立 `strategy_engine/factor_FX_inertia.py`：<br>- `InertiaEngine` 類別：資金流動慣性計算<br>- `__init__(target_groups)`：初始化目標族群列表<br>- `update_inertia(new_sai_residuals)`：EMA 更新（基於 Volume Bar 事件，非時鐘時間）<br>- `EMA_ALPHA = 0.33`：平滑係數（對應 N=5 根 Volume Bar）<br>- `F_Inertia(t) = α * SAI_Residual(t) + (1-α) * F_Inertia(t-1)`：遞迴計算公式<br>- `inertia_values`：Dict[str, float] 格式的狀態管理（族群名稱 → 當前慣性值）<br>- 輸出格式：`{"F_Inertia_AI_Concept": float, "F_Inertia_Semiconductor": float, ...}`<br>- 測試檔：`tests/strategy_engine/test_factor_FX_inertia.py`（需測試 EMA 更新、事件序列基礎計算） | `股神腦系統具體化設計_AI知識庫版_v1.md`<br>`股市大自然萬物修復法則_AI知識庫版_v1.md`<br>CapitalFlowEngine（Step 4）<br>InfoTimeEngine（Step 2） |
| 8 | 壓力傳導因子（F_PT） | 建立 `strategy_engine/factor_FX_pressure_transmission.py`：<br>- `PressureTransmissionEngine` 類別：壓力傳導計算<br>- `__init__(group_leader_map, window_bars=10, max_lead_lag=3, moi_threshold=0.5, sai_threshold=0.5)`：初始化參數<br>- `update_bar(group_moi, group_sai_residual)`：更新 Volume Bar 數據<br>- `_compute_pt_for_group(group)`：計算特定族群的 F_PT<br>- `history`：Dict[str, deque] 格式的歷史序列管理（族群名稱 → (MOI, SAI_Residual) 序列）<br>- `lead_score`：領先程度計算（龍頭 MOI 顯著事件 → 族群 SAI 顯著的比例）<br>- `agree_score`：方向一致性計算（sign(MOI_t) * sign(SAI_t+lag) 的平均值）<br>- `F_PT = max(0.0, avg_lead * avg_agree)`：最終分數計算（負值剪成 0）<br>- 輸出格式：`{"F_PT_AI_Concept": float, "F_PT_Semiconductor": float, ...}`<br>- 測試檔：`tests/strategy_engine/test_factor_FX_pressure_transmission.py`（需測試領先-滯後分析、方向一致性） | `股神腦系統具體化設計_AI知識庫版_v1.md`<br>CapitalFlowEngine（Step 4）<br>XQ API（龍頭股 MOI 數據）<br>InfoTimeEngine（Step 2） |
| 9 | 主力意圖逆轉因子（F_MRR） | 建立 `strategy_engine/factor_FX_major_reversal_risk.py`：<br>- `MajorReversalRiskEngine` 類別：主力逆轉風險計算<br>- `update_bar(major_stats)`：更新 Tick 級別主力數據<br>- `_calculate_cancel_rate(symbol, major_buy_volume, major_sell_volume, major_cancel_volume)`：撤單率計算<br>- `CancelRate_Major = (主力大單取消量) / (主力大單掛出量)`：核心公式<br>- `_detect_rapid_cancellation(cancel_sequence, time_window_seconds=10)`：短時間內連續撤單偵測<br>- `_calculate_mrr_score(cancel_rate, rapid_cancel_flag)`：F_MRR 分數計算（0~1，越高代表逆轉風險越高）<br>- `major_stats` 格式：`{"2330": {"major_buy_volume": float, "major_sell_volume": float, "major_cancel_volume": float, ...}, ...}`<br>- 輸出格式：`{"F_MRR_2330": float, "F_MRR_2317": float, ...}`<br>- 與 Reward Engine 整合：F_MRR 高時，RL 在「繼續加碼」行為上會被重罰<br>- 測試檔：`tests/strategy_engine/test_factor_FX_major_reversal_risk.py`（需測試撤單率計算、連續撤單偵測） | `股神腦系統具體化設計_AI知識庫版_v1.md`<br>XQ API（Tick 級別訂單簿數據、撤單數據）<br>InfoTimeEngine（Step 2） |
| 10 | 因子正交化引擎（O-Factor） | 建立 `strategy_engine/factor_orthogonalizer.py`：<br>- `FactorOrthogonalizer` 類別：PCA 正交化引擎<br>- `__init__(n_components=4)`：初始化 PCA 模型（輸出 O_1~O_4 四個正交因子）<br>- `fit(factor_matrix)`：歷史因子樣本訓練 PCA 模型（factor_matrix: np.ndarray, shape=(n_samples, n_features)）<br>- `transform(raw_factors)`：原始因子 → 正交因子轉換（輸入：Dict[str, float]，輸出：Dict[str, float]）<br>- `fit_from_factor_history(factor_history_df)`：從歷史 DataFrame 自動擬合（factor_history_df 包含所有原始因子欄位）<br>- 輸入因子類別：F_C（資金流）、F_S（技術面）、F_D（微觀結構）、F_XA（跨資產）<br>- 輸出格式：`{"O_1": float, "O_2": float, "O_3": float, "O_4": float}`（正交化後的因子，無共線性）<br>- `explained_variance_ratio_`：PCA 解釋變異比例（用於診斷因子重要性）<br>- 測試檔：`tests/strategy_engine/test_factor_orthogonalizer.py`（需測試 PCA 擬合、正交性驗證、解釋變異比例） | `股市聖經四_AI知識庫版_v1.md`<br>所有基礎因子引擎（Step 4-6）<br>所有強化因子引擎（Step 7-9） |
| 11 | 內部壓力因子（F_Internal） | 建立 `strategy_engine/factor_FX_internal.py`：<br>- `InternalPressureFactor` 類別：內部壓力計算<br>- `compute(orthogonal_factors)`：F_Internal 計算（輸入：O_1~O_4 正交因子）<br>- `W_i = |Z_i|`：權重計算（Z_i 為正交因子的 Z-score）<br>- `C = sum(W_i * sign(Z_i)) / sum(W_i)`：中心化常數<br>- `F_Internal = sum(W_i * (sign(Z_i) - C)^2) / sum(W_i)`：核心公式（衡量因子間內部衝突程度）<br>- `interpret_level(f_internal_value)`：壓力等級標籤（LOW: <0.3, MEDIUM: 0.3~0.7, HIGH: >0.7）<br>- `_calculate_zscore(factor_value, mean, std)`：Z-score 計算輔助函式<br>- 輸出格式：`{"F_Internal": float, "F_Internal_Level": str}`<br>- 整合到 Reward Function：`Reward = Sharpe - λDD * MaxDrawdown - λinternal * I(F_Internal>θ) * I(NetExposure>SafeLimit)`<br>- 測試檔：`tests/strategy_engine/test_factor_FX_internal.py`（需測試公式計算、壓力等級判斷） | `股市聖經四_AI知識庫版_v1.md`<br>FactorOrthogonalizer（Step 10）<br>正交化因子（O_1~O_4） |
| 12 | Transformer-RL State Vector | 建立 `rl_engine/state/state_builder.py` 與 `rl_engine/transformer_agent.py`：<br>- `StateBuilder` 類別：State Vector 建構器<br>- `__init__(price_feature_keys, technical_feature_keys, capital_flow_feature_keys)`：初始化欄位順序<br>- `build_state(price_features, technical_features, capital_flow_factors)`：組合成 np.ndarray（1D，dtype=np.float32）<br>- `state_dim`：State Vector 總維度（價格特徵數 + 技術指標數 + 資金流因子數）<br>- `TransformerAgent` 類別：Attention-based Transformer Model<br>- `__init__(state_dim, action_dim, hidden_dim=256, num_layers=3, num_heads=8)`：模型初始化<br>- `forward(state_sequence)`：前向傳播（輸入：np.ndarray, shape=(batch_size, seq_len, state_dim)）<br>- `predict_action(state_sequence)`：預測動作（輸出：np.ndarray, shape=(batch_size, action_dim)）<br>- State Vector 包含：價格特徵（close_norm, return_1d, ...）、技術指標（rsi_14, macd, ...）、F_C 系列（SAI_Residual_*, MOI, F_Inertia_*, F_PT_*, F_MRR_*）、F_Orderbook_*、F_CrossAsset_*、O_1~O_4<br>- 缺失值處理：用 0.0 填補<br>- 測試檔：`tests/rl_engine/test_state_builder.py`、`test_transformer_agent.py`（需測試 State Vector 建構、Transformer 前向傳播） | `股市聖經四_AI知識庫版_v1.md`<br>`股市大自然萬物修復法則_AI知識庫版_v1.md`<br>所有 Factor Engine（Step 4-11）<br>MicrostructureEngine（Step 3） |
| 13 | RL Reward & Memory Engine | 建立 `rl_engine/reward_engine.py` 與 `rl_engine/memory_engine.py`：<br>- `RewardEngine` 類別：Reward 計算引擎<br>- `compute(returns, drawdowns, f_internal, net_exposure, safe_limit)`：Reward 計算<br>- `Reward = λ1 * Sharpe - λDD * MaxDrawdown - λinternal * I(F_Internal>θ) * I(NetExposure>SafeLimit)`：核心公式<br>- `_calculate_sharpe_ratio(returns, risk_free_rate=0.0)`：Sharpe Ratio 計算<br>- `_calculate_max_drawdown(equity_curve)`：最大回撤計算<br>- `RLMemoryEngine` 類別：RL 記憶管理<br>- `__init__(capacity=10000, sequence_length=10)`：初始化 Replay Buffer<br>- `store_transition(state, action, reward, next_state, done)`：儲存 Transition（Transition dataclass：state, action, reward, next_state, done）<br>- `sample_batch(batch_size=32)`：隨機採樣批次（用於 off-policy RL 訓練）<br>- `get_sequence(symbol, length)`：取得短期序列記憶（用於 RNN/Transformer 輸入）<br>- `Transition` dataclass：`@dataclass class Transition: state: np.ndarray, action: np.ndarray, reward: float, next_state: np.ndarray, done: bool`<br>- 測試檔：`tests/rl_engine/test_reward_engine.py`、`test_memory_engine.py`（需測試 Reward 計算、Replay Buffer 採樣、序列記憶） | `股市聖經四_AI知識庫版_v1.md`<br>`雙引擎與自主演化閉環_AI知識庫版_v1.md`<br>InternalPressureFactor（Step 11）<br>StateBuilder（Step 12） |
| 14 | 診斷與修復引擎 | 建立 `diagnostic/analyzer.py` 與 `execution/recovery_agent.py`：<br>- `DiscrepancyAnalyzer` 類別：誤差分層歸因<br>- `analyze_discrepancy(predicted_return, actual_return, execution_cost)`：誤差分析<br>- `E_Exec = execution_cost`：執行誤差（滑價、延遲等）<br>- `E_Model = predicted_return - actual_return - E_Exec`：模型誤差（預測偏差）<br>- `RecoveryAgent` 類別：熔斷後智能恢復<br>- `__init__(circuit_breaker_threshold=0.1, recovery_steps=5)`：初始化參數<br>- `check_market_stability(vix_level, market_entropy, latency_zscore)`：市場穩定性檢查（外部環境 + 內部狀態雙重檢查）<br>- `recover_from_circuit_breaker(current_exposure, target_exposure)`：漸進式槓桿恢復（分 recovery_steps 步逐步恢復）<br>- `_calculate_latency_zscore(current_latency, historical_mean, historical_std)`：延遲 Z-score 計算<br>- `_check_external_environment(vix_level, market_entropy)`：外部環境檢查（VIX < 30, Entropy < threshold）<br>- `_check_internal_state(latency_zscore)`：內部狀態檢查（Latency_Zscore < 2.0）<br>- 與 RL Trainer 整合：自動觸發模型校準（當 E_Model 持續偏高時）<br>- 測試檔：`tests/diagnostic/test_analyzer.py`、`test_recovery_agent.py`（需測試誤差歸因、市場穩定性檢查、漸進式恢復） | `股市大自然萬物修復法則_AI知識庫版_v1.md`<br>`股市聖經四_AI知識庫版_v1.md`<br>Macro Engine（VIX、Entropy 數據）<br>RL Trainer（Step 13） |
| 15 | 實盤模擬與監測 | 建立 `execution/paper_trading_engine.py` 與 `monitoring/dashboard.py`：<br>- `PaperTradingEngine` 類別：模擬下單、滑價模型、PnL 追蹤<br>- `OrderRouter` 類別：智能訂單路由、TCA 預測、訂單拆分<br>- `RiskMonitor` 類別：實時風險監控、違規偵測、自動熔斷<br>- `Dashboard`：執行延遲監測、因子貢獻度可視化、策略績效分析<br>- 整合所有引擎，實現完整交易閉環 | `JGOD_STOCK_TRADING_BIBLE_v1_AI知識庫版_v1.md`<br>`股市聖經四_AI知識庫版_v1.md`<br>所有前置模組（Step 1-14） |

---

## 📊 模組依賴關係圖

```
Step 1 (數據管道)
    ↓
Step 2 (信息時間) → Step 7 (F_Inertia)
    ↓
Step 3 (微觀因子) → Step 12 (State Vector)
    ↓
Step 4 (資金流基礎 SAI/MOI) → Step 7 (F_Inertia) → Step 8 (F_PT)
    ↓
Step 5 (F_Orderbook) → Step 10 (正交化)
    ↓
Step 6 (F_CrossAsset) → Step 10 (正交化)
    ↓
Step 7 (F_Inertia) → Step 10 (正交化)
    ↓
Step 8 (F_PT) → Step 10 (正交化)
    ↓
Step 9 (F_MRR) → Step 13 (Reward)
    ↓
Step 10 (正交化 O-Factor) → Step 11 (F_Internal) → Step 13 (Reward)
    ↓
Step 12 (State Vector) → Step 13 (RL) → Step 14 (診斷)
    ↓
Step 15 (實盤模擬)
```

---

## 🎯 關鍵里程碑

- **Milestone 1（Step 1-3）**：數據基礎與時間引擎
- **Milestone 2（Step 4-6）**：基礎因子完整體系（SAI/MOI、F_Orderbook、F_CrossAsset）
- **Milestone 3（Step 7-9）**：時間/空間/風險強化因子（F_Inertia、F_PT、F_MRR）
- **Milestone 4（Step 10-11）**：因子正交化與內部感知（O-Factor、F_Internal）
- **Milestone 5（Step 12-13）**：RL 模型與學習機制（Transformer-RL、Reward & Memory）
- **Milestone 6（Step 14-15）**：診斷修復與實盤上線

---

## 📝 注意事項

1. 每個步驟都應建立對應的測試檔案
2. 所有模組需遵循統一的介面設計規範
3. 數據流必須可追溯、可審計
4. 所有公式與計算邏輯需與知識庫完全一致
5. 系統需具備完整的日誌與監控機制

---

*本 Roadmap 基於 11 本 AI 知識庫版完整內容生成，確保所有技術細節與架構設計的一致性。*

