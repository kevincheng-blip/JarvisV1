# J-GOD Path D Engine 技術規格

## 概述

Path D Engine 是一個基於強化學習（Reinforcement Learning）的 Governance 參數與超參數優化器。它透過 RL Agent 自動調整 Path B 的治理門檻，以最大化長期 reward（基於 Sharpe Ratio、Max Drawdown、Breach Ratio 等指標）。

## 核心概念

### State Space (狀態空間)

Path D 的狀態從 Path B Window Result 中提取，包含：

- **最新 Window 績效指標**：
  - `sharpe_last`: 最後一個 window 的 Sharpe Ratio
  - `max_drawdown_last`: 最後一個 window 的 Max Drawdown
  - `breach_ratio_last`: 最後一個 window 的 Governance Breach 比例

- **歷史平均指標**：
  - `avg_sharpe_3`: 最近 3 個 window 的平均 Sharpe
  - `avg_sharpe_5`: 最近 5 個 window 的平均 Sharpe
  - `avg_breach_ratio_3`: 最近 3 個 window 的平均 Breach Ratio
  - `avg_breach_ratio_5`: 最近 5 個 window 的平均 Breach Ratio

- **當前治理參數**：
  - `current_sharpe_floor`: 當前 Sharpe 門檻
  - `current_max_drawdown_limit`: 當前 Max Drawdown 限制
  - `current_turnover_limit`: 當前換手率限制
  - `current_te_max`: 當前追蹤誤差上限
  - `mode_id`: Mode ID (0=basic, 1=extreme)

狀態向量長度：12 維（float32）

### Action Space (動作空間)

Path D 的動作是對治理參數的調整量（delta）：

- `delta_sharpe_floor`: Sharpe 門檻調整量
- `delta_max_drawdown_limit`: Max Drawdown 限制調整量
- `delta_turnover_limit`: 換手率限制調整量
- `delta_te_max`: 追蹤誤差上限調整量
- `delta_mode_logit`: Mode 傾向（>0 傾向 extreme, <0 傾向 basic）

動作向量長度：5 維（float32）

### Reward Function (獎勵函數)

Reward 設計如下：

```
base = sharpe

if max_drawdown_abs > 10:
    penalty_dd = -0.1 * ((max_drawdown_abs - 10) / 5.0)
else:
    penalty_dd = 0.0

penalty_breach = -5.0 * breach_ratio

if avg_turnover > 80:
    penalty_turnover = -0.01 * (avg_turnover - 80)
else:
    penalty_turnover = 0.0

reward = base + penalty_dd + penalty_breach + penalty_turnover
```

Reward 鼓勵：
- 高 Sharpe Ratio
- 低 Max Drawdown（< 10% 無 penalty）
- 低 Breach Ratio（重要，penalty 係數 5.0）
- 適中的換手率（< 80% 無 penalty）

### RL Agent (簡化版)

Path D 使用簡化的 Policy Gradient 方法（REINFORCE）：

- **策略**：線性高斯策略
  - `action = W @ state + b + gaussian_noise`
  
- **參數**：
  - `W`: 狀態到動作的權重矩陣 (state_dim × action_dim)
  - `b`: 偏差向量 (action_dim)

- **訓練**：
  - 收集一個 episode 的 transitions
  - 計算 discounted cumulative returns
  - 使用 REINFORCE 更新策略參數

**注意**：這是簡化版實作，未來可以替換成更高級的 RL 演算法（例如 PPO、SAC）。

## API 定義

### PathDTrainConfig

```python
@dataclass
class PathDTrainConfig:
    experiment_name: str
    data_source: Literal["mock", "finmind"]
    mode: Literal["basic", "extreme"]
    base_path_b_config: Dict[str, Any]  # 基礎 Path B 配置
    episodes: int = 100
    max_steps_per_episode: int = 10
    gamma: float = 0.99
    learning_rate: float = 0.001
    seed: int = 42
```

### PathDRunConfig

```python
@dataclass
class PathDRunConfig:
    experiment_name: str
    data_source: Literal["mock", "finmind"]
    mode: Literal["basic", "extreme"]
    base_path_b_config: Dict[str, Any]
    eval_episodes: int = 5
    max_steps_per_episode: int = 10
    policy_path: str  # 已訓練 policy 的路徑
```

### PathDEngine

```python
class PathDEngine:
    def train(self, config: PathDTrainConfig) -> PathDTrainResult:
        """執行 RL 訓練"""
    
    def evaluate(self, run_config: PathDRunConfig) -> PathDRunResult:
        """評估已訓練的 policy"""
```

## 與 Path B 的互動流程

### 訓練流程

1. **初始化**：
   - 初始化 RL Agent（隨機策略參數）
   - 設定初始治理參數（`sample_initial_params()`）

2. **Episode 迴圈**（每個 episode）：
   - **Step 迴圈**（每個 step）：
     a. 使用當前治理參數建立 Path B Config
     b. 執行 Path B Engine（限制 window 數量以加速）
     c. 從 Path B 結果提取績效指標
     d. 建立 RL State
     e. Agent 選擇動作（調整治理參數）
     f. 應用動作，得到新的治理參數
     g. 計算 Reward
     h. 記錄 Transition (state, action, reward, next_state)
   - Episode 結束後，訓練 Agent（REINFORCE 更新）

3. **儲存最佳 Policy**：
   - 追蹤最佳 episode reward
   - 儲存最佳 policy 到檔案（`.npz` 格式）

### 評估流程

1. **載入 Policy**：
   - 從檔案載入已訓練的 Agent 參數

2. **評估 Episode 迴圈**：
   - 使用確定性策略（deterministic=True）
   - 執行 Path B 並收集 metrics
   - 計算平均績效指標

## 輸出格式

### 訓練結果 (PathDTrainResult)

```python
{
    "config": PathDTrainConfig,
    "episode_rewards": List[float],
    "metrics": {
        "avg_reward": float,
        "best_reward": float,
        "final_reward": float,
    },
    "best_policy_path": str,
}
```

### 評估結果 (PathDRunResult)

```python
{
    "config": PathDRunConfig,
    "episode_rewards": List[float],
    "metrics": {
        "avg_sharpe": float,
        "avg_max_drawdown": float,
        "avg_breach_ratio": float,
        ...
    },
}
```

## 檔案結構

```
jgod/path_d/
├── __init__.py
├── path_d_types.py          # 型別定義
├── rl_state_encoder.py      # State 編碼器
├── rl_action_space.py       # Action 空間
├── rl_reward.py             # Reward 函數
├── rl_agent.py              # RL Agent (簡化版)
├── rl_training_loop.py      # 訓練迴圈
└── path_d_engine.py         # 主引擎

scripts/
└── run_jgod_path_d.py       # CLI 腳本

tests/path_d/
├── __init__.py
├── test_path_d_engine_smoke.py
├── test_state_encoder.py
└── test_reward_function.py
```

## 注意事項

1. **簡化版 RL**：目前使用簡化的 REINFORCE 演算法，未來可以升級到更先進的方法。

2. **訓練時間**：每次 step 需要執行 Path B，訓練時間可能較長。建議：
   - 限制 window 數量（例如最多 3 個 windows）
   - 使用 mock 資料進行快速迭代
   - 使用真實資料進行最終驗證

3. **參數範圍**：Action 應用後會 clip 到合理範圍：
   - `sharpe_floor`: [-1.0, 3.0]
   - `max_drawdown_limit`: [5.0, 40.0]%
   - `turnover_limit`: [10.0, 200.0]
   - `te_max`: [1.0, 10.0]%

## 參考文件

- `docs/JGOD_PATH_D_STANDARD_v1.md`: Path D 標準文件（非技術版本）
- `docs/JGOD_PATH_D_EDITOR_INSTRUCTIONS.md`: 編輯指南
- `spec/JGOD_PathBEngine_Spec.md`: Path B 技術規格

