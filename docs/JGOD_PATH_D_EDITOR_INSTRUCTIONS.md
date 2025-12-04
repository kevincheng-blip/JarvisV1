# Path D Editor Instructions

本文檔說明如何在 Editor 模式下修改和擴充 Path D Engine。

---

## 📁 檔案結構

```
jgod/path_d/
├── path_d_types.py          # 型別定義（State, Action, Config）
├── rl_state_encoder.py      # State 編碼器
├── rl_action_space.py       # Action 空間（參數調整邏輯）
├── rl_reward.py             # Reward 函數
├── rl_agent.py              # RL Agent（可替換）
├── rl_training_loop.py      # 訓練迴圈
└── path_d_engine.py         # 主引擎（API 入口）
```

---

## 🔧 常見修改場景

### 1. 新增 Action 維度

**目標**：讓 Agent 可以調整更多參數

**步驟**：

1. 修改 `path_d_types.py` 的 `PathDAction`：
   ```python
   @dataclass
   class PathDAction:
       # ... 現有欄位 ...
       delta_new_param: float = 0.0  # 新增欄位
   ```

2. 修改 `rl_action_space.py` 的 `apply_action_to_params()`：
   ```python
   def apply_action_to_params(...):
       # ... 現有邏輯 ...
       new_param = current_params.get("new_param", 0.0) + action.delta_new_param * scale
       new_params["new_param"] = np.clip(new_param, min_val, max_val)
   ```

3. 更新 `rl_agent.py` 的 `action_dim`：
   ```python
   action_dim = 6  # 從 5 改為 6
   ```

4. 在 `rl_state_encoder.py` 中，如果新參數需要加入 state，更新 `PathDState` 和 `encode_state_to_vector()`。

### 2. 調整 Reward 權重

**目標**：改變 Agent 的學習目標

**步驟**：

修改 `rl_reward.py` 的 `compute_reward()` 函數：

```python
def compute_reward(...):
    base = sharpe
    
    # 調整 penalty 係數
    penalty_breach = -10.0 * breach_ratio  # 從 -5.0 改為 -10.0（更重視 breach）
    
    # 或新增其他指標
    penalty_new_metric = -0.5 * new_metric
    
    reward = base + penalty_dd + penalty_breach + penalty_turnover + penalty_new_metric
    return reward
```

### 3. 擴充 State Space

**目標**：讓 Agent 觀察更多資訊

**步驟**：

1. 修改 `path_d_types.py` 的 `PathDState`：
   ```python
   @dataclass
   class PathDState:
       # ... 現有欄位 ...
       new_metric: float = 0.0  # 新增欄位
   ```

2. 修改 `rl_state_encoder.py` 的 `build_pathd_state_from_pathb()`：
   ```python
   def build_pathd_state_from_pathb(...):
       # ... 現有邏輯 ...
       new_metric = extract_from_window_result(window_result)
       state = PathDState(..., new_metric=new_metric)
   ```

3. 修改 `encode_state_to_vector()`：
   ```python
   def encode_state_to_vector(state: PathDState) -> np.ndarray:
       vector = np.array([
           # ... 現有欄位 ...
           state.new_metric,  # 新增
       ], dtype=np.float32)
   ```

4. 更新 `rl_agent.py` 的 `state_dim` 和 `rl_training_loop.py` 的 state_dim 設定。

### 4. 升級 RL 演算法

**目標**：替換簡化版 REINFORCE 為更先進的方法

**步驟**：

1. 建立新的 Agent 類別（例如 `PPOAgent`）：
   ```python
   class PPOAgent:
       def __init__(self, state_dim, action_dim, ...):
           # 使用 PyTorch 實作
           ...
       
       def select_action(self, state, deterministic=False):
           ...
       
       def train_step(self):
           ...
   ```

2. 修改 `rl_agent.py`，將 `SimpleGaussianPolicyAgent` 替換為新實作，或保留兩個選項：
   ```python
   # 在 __init__.py 中
   from jgod.path_d.rl_agent import SimpleGaussianPolicyAgent
   # 或
   from jgod.path_d.rl_agent_ppo import PPOAgent
   ```

3. 更新 `rl_training_loop.py` 和 `path_d_engine.py` 中的 Agent 初始化。

**注意**：升級到深度學習框架（PyTorch/TensorFlow）後，需要更新依賴項。

### 5. 調整參數範圍

**目標**：改變 Agent 可調整的參數範圍

**步驟**：

修改 `rl_action_space.py` 的 `apply_action_to_params()` 中的 clip 範圍：

```python
# 例如：放寬 Sharpe 門檻範圍
new_sharpe_floor = np.clip(new_sharpe_floor, -2.0, 5.0)  # 從 [-1.0, 3.0] 改為 [-2.0, 5.0]
```

### 6. 修改訓練迴圈邏輯

**目標**：改變訓練流程（例如加入驗證階段）

**步驟**：

修改 `rl_training_loop.py` 的 `train_path_d()` 函數：

```python
def train_path_d(config: PathDTrainConfig) -> PathDTrainResult:
    # ... 現有訓練迴圈 ...
    
    # 每 N 個 episode 執行一次驗證
    if episode % 10 == 0:
        validation_reward = evaluate_on_validation_set(agent, validation_config)
        logger.info(f"Validation reward: {validation_reward:.2f}")
```

---

## 🧪 測試建議

修改後，建議執行以下測試：

1. **單元測試**：
   ```bash
   PYTHONPATH=. pytest tests/path_d/test_state_encoder.py -v
   PYTHONPATH=. pytest tests/path_d/test_reward_function.py -v
   ```

2. **Smoke Test**：
   ```bash
   PYTHONPATH=. pytest tests/path_d/test_path_d_engine_smoke.py -v
   ```

3. **完整測試**：
   ```bash
   PYTHONPATH=. pytest tests/path_d -q -v
   ```

---

## 📝 程式碼風格

請遵循以下規範：

1. **型別註解**：所有函數參數和返回值都要有型別註解
2. **Docstring**：所有公開函數和類別都要有 docstring
3. **PEP 8**：遵循 Python 程式碼風格規範
4. **註解**：在複雜邏輯處加上註解說明

---

## 🔍 Debug 技巧

### 1. 檢查 State 向量

在 `rl_state_encoder.py` 中加入 debug print：

```python
def encode_state_to_vector(state: PathDState) -> np.ndarray:
    vector = ...
    if np.isnan(vector).any():
        logger.warning(f"NaN detected in state vector: {vector}")
    return vector
```

### 2. 檢查 Reward 計算

在 `rl_reward.py` 中加入詳細日誌：

```python
def compute_reward(...):
    reward = ...
    logger.debug(f"Reward breakdown: base={base}, penalty_dd={penalty_dd}, ...")
    return reward
```

### 3. 檢查 Agent 動作

在 `rl_training_loop.py` 中加入動作統計：

```python
action_vec = agent.select_action(state_vec)
logger.debug(f"Action: {action_vec}, Mean: {action_vec.mean()}, Std: {action_vec.std()}")
```

---

## 📚 參考資源

- **RL 基礎**：[Reinforcement Learning: An Introduction](http://incompleteideas.net/book/)
- **Policy Gradient**：[Policy Gradient Methods](https://spinningup.openai.com/en/latest/algorithms/vpg.html)
- **Path B 規格**：`spec/JGOD_PathBEngine_Spec.md`

---

## ⚠️ 重要提醒

1. **保持向後兼容**：修改時盡量不破壞現有 API
2. **更新文件**：修改後記得更新相關文件
3. **測試覆蓋**：新增功能時，記得新增對應的測試
4. **版本控制**：重大變更時，考慮增加版本號

