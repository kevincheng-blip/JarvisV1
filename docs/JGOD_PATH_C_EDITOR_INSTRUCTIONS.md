# Path C Engine Editor Instructions

## 📝 給未來 Editor 的使用說明

本文檔說明如何新增 scenario、執行實驗、以及解讀輸出結果。

---

## 🆕 如何新增 Scenario

### 方法 1: 修改 scenario_presets.py

編輯 `jgod/path_c/scenario_presets.py`，在 `get_default_scenarios_for_taiwan_equities()` 函數中新增 scenario：

```python
scenarios.append(PathCScenarioConfig(
    name="my_new_scenario",
    description="My new scenario description",
    start_date="2023-01-01",
    end_date="2023-12-31",
    rebalance_frequency="M",
    universe=["2330.TW", "2317.TW"],
    walkforward_window="6m",
    walkforward_step="1m",
    data_source="mock",
    mode="basic",
    regime_tag="custom",
))
```

### 方法 2: 使用 JSON Config 檔

建立一個 JSON 檔案，例如 `my_scenarios.json`：

```json
{
  "scenarios": [
    {
      "name": "scenario_1",
      "description": "My first scenario",
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "rebalance_frequency": "M",
      "universe": ["2330.TW", "2317.TW"],
      "walkforward_window": "6m",
      "walkforward_step": "1m",
      "data_source": "mock",
      "mode": "basic",
      "regime_tag": "custom"
    }
  ]
}
```

然後執行：

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_c.py \
  --name my_experiment \
  --config my_scenarios.json
```

---

## 🚀 如何執行實驗

### 基本執行

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_c.py \
  --name demo_path_c \
  --output-dir output/path_c
```

### 使用自訂 Config

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_c.py \
  --name custom_experiment \
  --config path/to/scenarios.json \
  --output-dir output/path_c
```

---

## 📊 如何解讀輸出結果

### 1. 查看 CSV 排名表

打開 `output/path_c/{experiment_name}/scenarios_rankings.csv`：

- `rank`: 排名（1 為最佳）
- `sharpe`: Sharpe Ratio（越高越好）
- `max_drawdown`: 最大回撤（越小越好）
- `governance_breach_ratio`: Breach 比例（越低越好）

### 2. 查看 JSON 總結

打開 `path_c_summary.json`，可以找到：

- `best_scenarios`: 最佳 Scenario 名稱列表
- `ranking_table`: 完整排名表
- 每個 Scenario 的詳細結果

### 3. 查看 Markdown 報告

打開 `path_c_report.md`，包含：

- 實驗基本資訊
- 前 3 名 Scenario 的詳細分析
- 所有 Scenarios 的摘要表格

---

## 🔍 常見問題

### Q: 如何知道哪個 Scenario 最適合上線？

A: 查看排名表，優先考慮：
1. Sharpe Ratio 高
2. Max Drawdown 小
3. Governance Breach 比例低

### Q: 如何比較不同 Mode 的表現？

A: 在 CSV 中查看 `mode` 欄位，比較 `basic` 和 `extreme` 模式下的相同設定。

### Q: 如何測試不同的治理門檻？

A: 在 Scenario Config 中設定 `max_drawdown_limit`、`min_sharpe` 等參數，建立多個 Scenario 進行比較。

---

## 📚 參考文件

- `spec/JGOD_PathCEngine_Spec.md`: 技術規格
- `docs/JGOD_PATH_C_STANDARD_v1.md`: 標準文件

