# 使用說明

## 安裝

```bash
pip install -r requirements.txt
```

## 環境變數設定

建立 `.env` 檔案，設定以下環境變數：

```env
# OpenAI
OPENAI_API_KEY=your_key

# Claude
ANTHROPIC_API_KEY=your_key

# Gemini
GOOGLE_API_KEY=your_key

# Perplexity
PERPLEXITY_API_KEY=your_key

# FinMind
FINMIND_TOKEN=your_token
```

## CLI 使用

### 系統狀態

```bash
python -m jgod status
```

### 掃描專案

```bash
# 簡單掃描
python -m jgod scan

# 產生系統地圖
python -m jgod scan --write-report
```

### 交易模擬

```bash
python -m jgod trade simulate
```

### AI 戰情室

```bash
python -m jgod warroom --question "2330 值得買嗎？" --stock-id "2330"
```

### 提取 TODO

```bash
python -m jgod todo
python -m jgod todo --output docs/TODO.md
```

### 系統洞察

```bash
python -m jgod insight
python -m jgod insight --output docs/insight.md
```

## Streamlit Web UI

### 啟動

```bash
python main.py
```

或

```bash
streamlit run jgod/war_room/war_room_app.py
```

### 功能

- 股票資料查詢
- AI 戰情室諮詢
- 多 AI 提供者選擇
- 交易決策建議

## 模組開發

### 新增策略

1. 繼承 `BaseStrategy`
2. 實作 `generate_signal` 方法
3. 在策略引擎中註冊

```python
from jgod.strategy import BaseStrategy, Signal, SignalType

class MyStrategy(BaseStrategy):
    def generate_signal(self, symbol, data, current_price=None):
        # 實作策略邏輯
        return Signal(...)
```

### 新增 AI 提供者

1. 在 `api_clients/` 建立新的 client
2. 實作 `ask` 方法
3. 在 `PROVIDER_REGISTRY` 中註冊

## 部署

### Docker

```bash
docker build -t jgod .
docker run -p 8000:8000 jgod
```

### Zeabur

專案已包含 Dockerfile，可直接部署到 Zeabur。

## 注意事項

1. 本系統為模擬交易系統，不提供實際交易功能
2. AI 建議僅供參考，不構成投資建議
3. 請妥善保管 API 金鑰
4. 建議在開發環境測試後再部署

