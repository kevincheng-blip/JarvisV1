# J-GOD Path D Standard v1.0

## 📋 概述

Path D 是一個 **基於強化學習（RL）的 Governance 參數與超參數優化器**。它透過 RL Agent 自動調整 Path B 的治理門檻（例如 Sharpe 門檻、Max Drawdown 限制、換手率上限等），以最大化長期 reward。

### 核心價值

傳統上，治理參數需要手動調整或透過網格搜尋（Grid Search）來找到最佳組合。Path D 使用強化學習自動學習：

- 在什麼市場環境下，應該放寬或收緊治理門檻
- 如何平衡風險與報酬（Sharpe vs Max Drawdown）
- 如何降低 Governance Breach 比例

### 與 Path A / Path B / Path C 的關係

```
Path A (Alpha Engine)
    ↓
Path B (Walk-Forward + Governance)
    ↓
Path D (RL-based Parameter Tuning) ← 優化 Path B 的治理參數
    ↓
Path C (Scenario Validation) ← 使用優化後的參數進行批量驗證
```

Path D 的目標是**自動找到最佳治理參數組合**，讓 Path B 的策略表現更好。

---

## 🎯 核心概念

### 1. State（狀態）

Path D Agent 觀察的狀態包含：

- **最新績效指標**：Sharpe Ratio、Max Drawdown、Breach Ratio
- **歷史趨勢**：最近 3 個和 5 個 window 的平均表現
- **當前設定**：當前的治理門檻值

### 2. Action（動作）

Agent 可以調整的參數：

- **Sharpe 門檻**：提高或降低最低 Sharpe 要求
- **Max Drawdown 限制**：放寬或收緊最大回撤限制
- **換手率上限**：調整年化換手率限制
- **追蹤誤差上限**：調整 TE 限制
- **模式選擇**：在 Basic 和 Extreme 模式之間切換

### 3. Reward（獎勵）

Reward 設計鼓勵：

- ✅ 高 Sharpe Ratio
- ✅ 低 Max Drawdown（< 10% 無 penalty）
- ✅ 低 Breach Ratio（重要，penalty 係數 5.0）
- ✅ 適中的換手率（< 80% 無 penalty）

---

## 🚀 使用方式

### 訓練 Path D Agent

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_d.py train \
    --name my_experiment \
    --config configs/path_d/train_config.json \
    --output-dir output/path_d
```

訓練完成後，最佳 policy 會儲存在 `models/path_d/{experiment_name}/best_policy.npz`。

### 評估已訓練的 Agent

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_d.py eval \
    --name my_experiment \
    --config configs/path_d/eval_config.json \
    --policy-path models/path_d/my_experiment/best_policy.npz \
    --output-dir output/path_d
```

評估結果會輸出到 `output/path_d/{experiment_name}/eval_result.json`。

---

## 📊 配置檔案格式

### 訓練配置 (train_config.json)

```json
{
    "experiment_name": "path_d_demo",
    "data_source": "mock",
    "mode": "basic",
    "base_path_b_config": {
        "train_start": "2020-01-01",
        "train_end": "2022-12-31",
        "test_start": "2023-01-01",
        "test_end": "2023-12-31",
        "walkforward_window": "6m",
        "walkforward_step": "3m",
        "universe": ["AAPL", "GOOGL", "MSFT"],
        "rebalance_frequency": "M",
        "alpha_config_set": [
            {
                "name": "strategy_1",
                "alpha_config": {}
            }
        ],
        "data_source": "mock",
        "mode": "basic"
    },
    "episodes": 100,
    "max_steps_per_episode": 10,
    "gamma": 0.99,
    "learning_rate": 0.001,
    "seed": 42
}
```

### 評估配置 (eval_config.json)

與訓練配置相同格式，但不需要 `episodes`、`gamma`、`learning_rate`、`seed`，而是需要 `eval_episodes` 和 `policy_path`。

---

## 📈 結果解讀

### 訓練結果

訓練完成後，你會得到：

- **episode_rewards**: 每個 episode 的累積 reward
- **metrics**:
  - `avg_reward`: 平均 reward
  - `best_reward`: 最佳 episode reward
  - `final_reward`: 最後一個 episode 的 reward

**理想狀況**：reward 應該隨訓練逐漸上升，表示 Agent 正在學習更好的參數調整策略。

### 評估結果

評估完成後，你會得到：

- **episode_rewards**: 每個評估 episode 的 reward
- **metrics**:
  - `avg_sharpe`: 平均 Sharpe Ratio
  - `avg_max_drawdown`: 平均 Max Drawdown
  - `avg_breach_ratio`: 平均 Breach Ratio
  - `avg_turnover`: 平均換手率

**比較建議**：
- 與未優化的基準（baseline）比較
- 觀察 Breach Ratio 是否下降
- 觀察 Sharpe Ratio 是否提升

---

## ⚠️ 注意事項

### 1. 訓練時間

Path D 的訓練時間取決於：

- **Episodes 數量**：每個 episode 都需要執行 Path B
- **Steps per episode**：每個 step 都需要執行 Path B
- **Window 數量**：Path B 的 window 數量越多，執行時間越長

**建議**：
- 快速迭代：使用 `mock` 資料、減少 episodes 和 steps
- 最終驗證：使用真實資料、完整 episodes 和 steps

### 2. 簡化版 RL

Path D 目前使用簡化的 REINFORCE 演算法（只用 numpy，不依賴深度學習框架）。這是一個**簡化版實作**，適合：

- 快速原型開發
- 小規模實驗
- 理解 RL 基本概念

對於生產環境，建議升級到更先進的 RL 演算法（例如 PPO、SAC）。

### 3. 參數範圍

Agent 調整的參數會被 clip 到合理範圍：

- Sharpe 門檻：[-1.0, 3.0]
- Max Drawdown 限制：[5.0%, 40.0%]
- 換手率限制：[10.0, 200.0]
- 追蹤誤差上限：[1.0%, 10.0%]

這些範圍可以在 `rl_action_space.py` 中調整。

---

## 📚 進階使用

### 自訂 Reward 函數

修改 `jgod/path_d/rl_reward.py` 中的 `compute_reward()` 函數，調整 penalty 係數或增加新的指標。

### 擴充 Action Space

在 `jgod/path_d/path_d_types.py` 中新增 `PathDAction` 欄位，並在 `rl_action_space.py` 中實作對應的調整邏輯。

### 升級 RL 演算法

在 `jgod/path_d/rl_agent.py` 中，你可以替換 `SimpleGaussianPolicyAgent` 為更高級的實作（例如使用 PyTorch 實作 PPO）。

---

## 📖 參考文件

- `spec/JGOD_PathDEngine_Spec.md`: 技術規格（詳細 API 定義）
- `docs/JGOD_PATH_D_EDITOR_INSTRUCTIONS.md`: 編輯指南（如何修改 Path D）
- `spec/JGOD_PathBEngine_Spec.md`: Path B 技術規格（Path D 的底層依賴）

---

## 🔄 下一步

1. **完成訓練**：使用 mock 資料進行快速迭代，找到最佳 hyperparameters
2. **真實資料驗證**：使用 FinMind 真實資料進行最終驗證
3. **整合到 Path C**：將優化後的參數用於 Path C 的場景驗證
4. **升級 RL 演算法**：考慮升級到更先進的方法（例如 PPO、SAC）

