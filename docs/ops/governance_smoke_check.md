# Governance Smoke Check (Backend + Frontend)

最小驗收流程，確認治理摘要 API 與前端 AI Action Card 可正常顯示。

## 1) 啟動後端
```bash
cd /Users/kevincheng/JarvisV1
source .venv/bin/activate
uvicorn jgod.api.main:app --port 8000
```

## 2) 驗證治理摘要 API
```bash
curl -s http://127.0.0.1:8000/api/v1/governance/summary | jq .
```
預期：HTTP 200，包含 `drift_status`, `execution_confidence`, `cluster_risk`, `regime`, `market_complexity`, `ai_action`, `updated_at`, `is_stub`，`ai_action` 為 enum，`reasons` 為 list。

## 3) 啟動前端並檢視 AI Action Card
```bash
cd /Users/kevincheng/JarvisV1/trading-ui/jgod-trading-ui
npm run dev
```
在瀏覽器開啟 `http://localhost:3000/`，Dashboard 應顯示 AI Action 卡片（PanelBoundary 包裹），即使為 placeholder/stub 亦應正常渲染且無 runtime error。


