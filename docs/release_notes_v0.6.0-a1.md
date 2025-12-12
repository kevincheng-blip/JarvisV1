# J-GOD v0.6.0-A1 Release Notes

**發布日期：** 2025-12-13  
**版本：** v0.6.0-A1

---

## 亮點 (Highlights)

此版本 (v0.6.0-A1) 新增 **Decision Engine V3**，整合 S-Rank V2 推薦系統與 Performance Feed，提供規則驅動的決策建議：

- **Decision Engine V3**：基於 S-Rank V2 推薦與績效指標的決策引擎
- **風險管理**：自動計算 position_scale 與 risk_state（RISK_ON / CAUTION / RISK_OFF）
- **決策信心度**：基於穩定性與策略權重計算 confidence（0.0 ~ 1.0）
- **決策說明**：自動生成繁中決策摘要（包含模式、主要策略、風險狀態、理由）
- **War Room V2 整合**：新增 DecisionV3Card 顯示決策結果

---

## 新增/更新端點 (New/Updated Endpoints)

### 新增後端 API
- `GET /api/v1/decision-v3/decide/{symbol}?mode=performance&limit=60&k=5`
  - 取得 Decision V3 決策結果
  - 參數：
    - `mode`: "performance" (預設) 或 "signals"
    - `limit`: 時間軸資料點數（預設 60）
    - `k`: 推薦策略數量（預設 5）
  - 回應：永不回 404，無資料時回 200 + RISK_OFF

### 新增前端 API Wrapper (in `trading-ui/jgod-trading-ui/src/api/client.ts`)
- `getDecisionV3(symbol, {mode, limit, k})`

---

## 驗證指令 (Verification Commands)

### 後端驗證
1. **語法檢查**
   ```bash
   python3 -m compileall jgod -q
   # 預期：無輸出（0 錯誤）
   ```

2. **Decision V3 合約測試**
   ```bash
   pytest tests/test_decision_v3_contract.py -q -v
   # 預期：2 passed
   ```

3. **完整 CI 檢查**
   ```bash
   bash scripts/ci_quick_check.sh
   # 預期：所有 9 個檢查通過
   ```

4. **手動 Curl 範例**
   ```bash
   # Decision V3 (Performance Mode)
   curl -i "http://127.0.0.1:8000/api/v1/decision-v3/decide/2330?mode=performance&limit=60&k=5"
   # 預期：200 OK, JSON 包含：
   #   - selected_primary_strategy
   #   - selected_secondary_strategies
   #   - risk_plan {position_scale, risk_state, reasons}
   #   - confidence
   #   - explain (繁中)
   
   # Decision V3 (Signals Mode)
   curl -i "http://127.0.0.1:8000/api/v1/decision-v3/decide/2330?mode=signals&limit=60&k=5"
   # 預期：200 OK
   
   # Decision V3 (NO_DATA case)
   curl -i "http://127.0.0.1:8000/api/v1/decision-v3/decide/NO_SYMBOL?mode=performance"
   # 預期：200 OK, risk_state="RISK_OFF", position_scale <= 0.25
   ```

### 前端驗證
1. **啟動開發伺服器**
   ```bash
   cd trading-ui/jgod-trading-ui && npm run dev
   ```

2. **導航至 War Room V2**
3. **驗證 DecisionV3Card**：
   - 應顯示在右側欄（SRankRecommendationCard 下方）
   - 顯示主要策略、建議倉位、信心度
   - 顯示風險狀態 badge（RISK_ON / CAUTION / RISK_OFF）
   - 顯示策略權重（Top 3）
   - 顯示風險理由與決策說明（多行）
   - 若無資料：顯示 "Decision V3 暫無資料"（非錯誤）

4. **點選不同股票**：
   - 點選 Top Predictions 中的股票
   - 驗證 DecisionV3Card 自動更新
   - 確認無 404 錯誤

---

## 已知限制 (Known Limitations)

- **決策邏輯**：目前為規則驅動（rule-based），尚未整合 ML/RL
- **風險計算**：position_scale 計算規則較簡單，未來可擴充為更複雜的風險模型
- **績效整合**：若 performance mode 無資料，會自動 fallback 到 signals mode
- **前端顯示**：DecisionV3Card 目前僅顯示基本資訊，未來可擴充為更詳細的決策樹視覺化

---

## 技術細節

### Decision V3 決策流程

1. **取得策略推薦**：呼叫 `jgod.s_rank_v2.service.get_recommendation()`
2. **選取主要/輔助策略**：Top1 為 primary，Top2-3 為 secondary（最多 2 個）
3. **計算風險計劃**：
   - 基於 stability_grade 設定 base position_scale
   - 若 performance mode 且 max_drawdown_proxy > 0.15，進一步降低
   - Clamp 到 [0.05, 1.0]
4. **計算信心度**：
   - Base = 0.5
   - Stability grade 調整：STABLE +0.25, WATCH +0.1, VOLATILE -0.15, NO_DATA -0.25
   - Top1 weight 調整：>= 0.45 +0.1, < 0.30 -0.1
   - Clamp 到 [0.0, 1.0]
5. **生成說明**：繁中摘要（<= 10 行）

### 風險狀態對應

- **RISK_ON**：STABLE，position_scale = 0.80
- **CAUTION**：WATCH (0.55) 或 VOLATILE (0.35)
- **RISK_OFF**：NO_DATA，position_scale = 0.20

---

**文件結束**

