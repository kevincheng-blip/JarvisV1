# J-GOD War Room / Execution API 安全盤點報告

**報告生成時間：** 2025-01-06  
**編撰者：** J-GOD 系統資安協作工程師（AI Assistant）  
**報告版本：** v1.0

---

## 一、掃描範圍與模組清單

### 1.1 已掃描的模組

本次盤點包含以下模組與專案範圍：

1. **`jgod/war_room_backend/`** - War Room Backend v5.0
   - `main.py` - FastAPI 主應用程式
   - `routers/war_room.py` - API 路由定義
   - `engine/war_room_engine.py` - 戰情室引擎
   - `websocket_manager.py` - WebSocket 連線管理器
   - `config.py` - 後端配置

2. **`jgod/war_room_backend_v6/`** - War Room Backend v6.0
   - `main.py` - FastAPI 主應用程式
   - `routers/war_room_ws.py` - WebSocket 路由定義
   - `websocket_manager.py` - WebSocket 連線管理器

3. **`jgod/execution/`** - 執行引擎模組
   - `virtual_broker.py` - 虛擬券商
   - `execution_engine.py` - 執行引擎
   - `trade_recorder.py` - 交易記錄器
   - 其他支援模組

4. **`jgod/api/main.py`** - 主要 Simulation API（參考）

### 1.2 掃描結果摘要

- **War Room Backend v5.0：** 3 個 endpoints（1 GET + 1 POST + 1 WebSocket）
- **War Room Backend v6.0：** 4 個 endpoints（2 GET + 1 POST + 1 WebSocket）
- **Execution 模組：** ❌ 無 HTTP/WebSocket API（純內部模組）
- **認證機制：** ❌ 完全無認證保護

---

## 二、所有 API / WebSocket Endpoint 清單

### 2.1 War Room Backend v5.0

**應用程式：** `jgod/war_room_backend/main.py`  
**預設 Port：** 8000（可透過環境變數 `WAR_ROOM_API_PORT` 設定）  
**預設 Host：** 0.0.0.0（可透過環境變數 `WAR_ROOM_API_HOST` 設定）

| 路徑 | 方法 | 檔案位置 | 用途說明 | 認證需求 | 備註 |
|------|------|----------|----------|----------|------|
| `/health` | GET | `jgod/war_room_backend/routers/war_room.py:19` | 健康檢查端點，回傳服務狀態 | ❌ **無認證** | 可被任何人存取 |
| `/api/war-room/session` | POST | `jgod/war_room_backend/routers/war_room.py:25` | 建立新的戰情室會話，產生 session_id | ❌ **無認證** | 任何人都可以建立 session |
| `/ws/war-room/{session_id}` | WebSocket | `jgod/war_room_backend/routers/war_room.py:32` | WebSocket 端點，接收戰情室請求並即時串流事件 | ❌ **無認證** | 任何人都可以連線，只需要知道 session_id |

### 2.2 War Room Backend v6.0

**應用程式：** `jgod/war_room_backend_v6/main.py`  
**預設 Port：** 8081（硬編碼在 `main.py:94`）  
**預設 Host：** 0.0.0.0（硬編碼在 `main.py:93`）

| 路徑 | 方法 | 檔案位置 | 用途說明 | 認證需求 | 備註 |
|------|------|----------|----------|----------|------|
| `/health` | GET | `jgod/war_room_backend_v6/main.py:64` | 健康檢查端點，回傳狀態、版本、活躍 session 數量、可用 providers | ❌ **無認證** | 暴露系統資訊（活躍 sessions、providers） |
| `/` | GET | `jgod/war_room_backend_v6/main.py:75` | 根路徑，回傳 API 資訊與可用端點列表 | ❌ **無認證** | 暴露 API 結構 |
| `/api/v6/war-room/session` | POST | `jgod/war_room_backend_v6/routers/war_room_ws.py:63` | 建立新的戰情室 Session（需要提供 stock_ids、mode、enabled_providers、user_prompt 等） | ❌ **無認證** | 任何人都可以建立 session 並觸發 AI 分析 |
| `/api/v6/war-room/ws/v6/war-room/{session_id}` | WebSocket | `jgod/war_room_backend_v6/routers/war_room_ws.py:86` | WebSocket 端點，接收請求並啟動戰情室引擎，推送即時事件流 | ❌ **無認證** | 任何人都可以連線，只需要知道 session_id |

**注意：** v6.0 的 WebSocket 路徑結構：
- Router prefix: `/api/v6/war-room`（定義在 `war_room_ws.py:22`）
- 端點路徑: `/ws/v6/war-room/{session_id}`（定義在 `war_room_ws.py:86`）
- **實際完整路徑：** `/api/v6/war-room/ws/v6/war-room/{session_id}`（路徑看起來有重複，建議未來優化）

### 2.3 Execution 模組

**掃描結果：** ❌ **無 HTTP/WebSocket API**

`jgod/execution/` 模組為純內部模組，不提供任何 HTTP 或 WebSocket 端點。該模組包含：
- `virtual_broker.py` - 虛擬券商類（純 Python 類）
- `execution_engine.py` - 執行引擎類（純 Python 類）
- `trade_recorder.py` - 交易記錄器類（純 Python 類）

這些模組僅供其他 Python 模組內部呼叫，不會暴露到網路上。

### 2.4 特別標記

#### 🔴 **不需要認證就能呼叫的 Endpoint（高風險）**

所有 War Room 相關的 endpoints **均無認證保護**：

1. **`GET /health`** (v5.0 & v6.0)
   - 任何人都可以檢查服務狀態
   - v6.0 版本還暴露活躍 sessions 和 providers 列表

2. **`GET /`** (v6.0)
   - 暴露 API 結構與可用端點

3. **`POST /api/war-room/session`** (v5.0)
   - 任何人都可以無限制建立 session

4. **`POST /api/v6/war-room/session`** (v6.0)
   - 任何人都可以無限制建立 session 並觸發 AI 分析（消耗 API 配額）

5. **`WebSocket /ws/war-room/{session_id}`** (v5.0)
   - 任何人只要知道 session_id 就可以連線並觸發 AI 分析

6. **`WebSocket /api/v6/war-room/ws/v6/war-room/{session_id}`** (v6.0)
   - 任何人只要知道 session_id 就可以連線並觸發 AI 分析（消耗 API 配額）
   - **注意：** 此路徑有重複的 `/ws/v6/war-room/`，實際完整路徑為 `/api/v6/war-room/ws/v6/war-room/{session_id}`

#### 🟡 **測試 / Demo / Debug 相關**

**未發現明顯的測試端點：**
- 無 `/test`、`/debug`、`/demo` 等明顯的測試端點
- 所有端點都是正式功能端點

**但需注意：**
- `/health` 端點在生產環境應限制存取或移除敏感資訊
- v6.0 的 `/health` 暴露了 `active_sessions` 和 `providers` 列表，屬於資訊洩漏風險

---

## 三、目前的安全性狀態

### 3.1 認證與授權機制

**現況：❌ 完全沒有任何形式的保護**

經過全面掃描，War Room Backend 模組中：
- ❌ **無 API Key 驗證**
- ❌ **無 Token 驗證（JWT、Bearer Token）**
- ❌ **無 Session 驗證**
- ❌ **無基本認證（Basic Auth）**
- ❌ **無 OAuth 整合**
- ❌ **無 Rate Limiting（雖然有 CORS 限制，但無請求頻率限制）**

**唯一的安全措施：**
- ✅ CORS 限制（僅允許 `http://localhost:3000` 和 `http://127.0.0.1:3000`）
- ⚠️ **但這個限制只在瀏覽器環境有效，如果直接透過 HTTP client（curl、Postman）或 Python requests 呼叫，CORS 不會生效**

### 3.2 風險評估（假設部署到外網）

如果將這些後端部署到外網（例如：`http://your-server.com:8000`），風險如下：

#### 🔴 **極高風險端點**

1. **`POST /api/war-room/session` 和 `POST /api/v6/war-room/session`**
   - **風險：** 任何人都可以無限制建立 session
   - **影響：** 
     - 消耗 API 配額（OpenAI、Anthropic、Gemini、Perplexity）
     - 造成資源浪費（記憶體、CPU）
     - 可能導致 API 費用暴增
   - **攻擊場景：** 攻擊者可以寫一個簡單的迴圈，不斷建立 session 並觸發 AI 分析，直到 API 配額用盡

2. **`WebSocket /ws/war-room/{session_id}` 和 `/api/v6/war-room/ws/v6/war-room/{session_id}`**
   - **風險：** 任何人都可以連線並觸發 AI 分析
   - **影響：**
     - 同上述，消耗 API 配額
     - 造成資源浪費
     - 如果攻擊者知道有效的 session_id，可以重複觸發分析
   - **攻擊場景：** 
     - 攻擊者可以先呼叫 `POST /session` 取得 session_id
     - 然後連線 WebSocket 並不斷發送請求觸發 AI 分析
     - 或者透過暴力猜測 UUID 格式的 session_id（雖然機率低，但理論上可行）

3. **`GET /health` (v6.0)**
   - **風險：** 暴露系統內部狀態
   - **影響：**
     - 洩漏活躍 sessions 數量
     - 洩漏可用的 AI providers 列表
     - 可能被用於系統偵察（Reconnaissance）
   - **攻擊場景：** 攻擊者可以透過 `/health` 端點了解系統狀態，規劃後續攻擊

#### 🟡 **中風險端點**

4. **`GET /health` (v5.0) 和 `GET /` (v6.0)**
   - **風險：** 暴露 API 結構與版本資訊
   - **影響：** 資訊洩漏，可能被用於系統偵察
   - **攻擊場景：** 攻擊者可以了解 API 結構，找到更多可利用的端點

### 3.3 其他安全風險

1. **CORS 限制不足**
   - 雖然限制了 origins，但這只在瀏覽器環境有效
   - 直接透過 HTTP client 呼叫時，CORS 不會生效
   - 建議：CORS 只是第一層防護，不能作為唯一的安全措施

2. **無 Rate Limiting**
   - 任何人都可以無限制地呼叫 API
   - 可能導致 DoS（Denial of Service）攻擊
   - 建議：實作 Rate Limiting（例如：每個 IP 每分鐘最多 10 次請求）

3. **無請求大小限制**
   - WebSocket 和 POST 請求沒有明確的大小限制
   - 可能導致資源耗盡攻擊
   - 建議：設定合理的請求大小限制

4. **Session ID 可預測性**
   - 雖然使用 UUID v4，但如果 session_id 洩漏，任何人都可以使用
   - 建議：Session 應該有過期時間，並且應該與使用者身份綁定

5. **無日誌審計**
   - 雖然有 logging，但沒有明確的審計日誌
   - 建議：記錄所有 API 呼叫（包含 IP、時間、請求內容）以便事後追蹤

---

## 四、下一步安全建議

### 4.1 馬上就該做的事（立即執行，1-2 天內）

#### 🔴 **優先級 1：關閉或限制 Health Check 端點**

**建議：**
- 移除 `/health` 端點中的敏感資訊（v6.0 的 `active_sessions`、`providers`）
- 或者限制 `/health` 端點只能從特定 IP 存取
- 或者要求 `/health` 端點必須提供 API Key

**實作方式：**
- 修改 `jgod/war_room_backend_v6/main.py:64-72`，移除敏感資訊或加入 IP 白名單
- 修改 `jgod/war_room_backend/routers/war_room.py:19-22`，加入基本認證或移除端點

#### 🔴 **優先級 2：加上基本 API Key 驗證**

**建議：**
- 為所有 War Room endpoints 加上 API Key 驗證
- API Key 可以透過環境變數設定（例如：`WAR_ROOM_API_KEY`）
- 如果請求中沒有提供正確的 API Key，回傳 401 Unauthorized

**實作方式：**
- 使用 FastAPI 的 `HTTPBearer` 或 `APIKeyHeader` dependency
- 在每個 endpoint 加上 dependency 檢查

**範例程式碼結構：**
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("WAR_ROOM_API_KEY")
    if not expected_key or api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

@router.post("/api/war-room/session", dependencies=[Depends(verify_api_key)])
async def create_session():
    ...
```

#### 🟡 **優先級 3：加入 Rate Limiting**

**建議：**
- 使用 `slowapi` 或 `fastapi-limiter` 實作 Rate Limiting
- 限制每個 IP 每分鐘最多 10 次請求（可調整）
- WebSocket 連線限制每個 IP 最多 5 個同時連線

**實作方式：**
- 安裝 `slowapi`：`pip install slowapi`
- 在 FastAPI app 中加入 Rate Limiter middleware

---

### 4.2 1～2 週內可以做的事

#### 🟡 **優先級 1：統一 War Room 版本**

**建議：**
- 評估 v5.0 和 v6.0 的功能差異
- 統一為單一版本（建議保留 v6.0）
- 移除或標記舊版本為 deprecated

**好處：**
- 減少維護成本
- 減少安全漏洞表面積
- 統一安全策略

#### 🟡 **優先級 2：整合到單一後端**

**建議：**
- 考慮將 War Room Backend 整合到主要的 `jgod/api/main.py`
- 或者明確分離：一個 Production API、一個 War Room API
- 統一 CORS、認證、Rate Limiting 策略

**好處：**
- 統一管理安全設定
- 減少部署複雜度
- 更容易監控與審計

#### 🟡 **優先級 3：精簡路由結構**

**建議：**
- 修正 v6.0 的 WebSocket 路徑重複問題（`/api/v6/war-room/ws/v6/war-room/{session_id}`）
- 統一 API 路徑命名規範
- 移除不必要的根路徑端點（或加入認證）

#### 🟡 **優先級 4：加入 Session 過期機制**

**建議：**
- Session 應該有過期時間（例如：1 小時）
- 過期的 session 不應該被使用
- 定期清理過期的 sessions

**實作方式：**
- 在 `websocket_manager.py` 中加入 session 過期時間記錄
- 在建立 session 時記錄建立時間
- 在 WebSocket 連線時檢查 session 是否過期

#### 🟡 **優先級 5：加入請求大小限制**

**建議：**
- 限制 POST 請求大小（例如：最大 1MB）
- 限制 WebSocket 訊息大小（例如：最大 100KB）

**實作方式：**
- 使用 FastAPI 的 `Request` 物件檢查內容長度
- 或者使用 middleware 統一處理

---

### 4.3 之後再做的事（長期規劃）

#### 🟢 **優先級 1：實作完整的認證與授權系統**

**建議：**
- 實作 JWT（JSON Web Token）認證
- 或者實作 OAuth 2.0 整合
- 支援多使用者與角色權限（RBAC）

**實作方式：**
- 使用 `python-jose` 實作 JWT
- 或使用 `authlib` 實作 OAuth 2.0
- 建立使用者資料表與權限系統

#### 🟢 **優先級 2：API Gateway 整合**

**建議：**
- 使用 API Gateway（例如：Kong、AWS API Gateway、Nginx）作為統一入口
- 在 Gateway 層統一處理認證、Rate Limiting、日誌
- 後端 API 可以專注於業務邏輯

**好處：**
- 統一安全策略
- 更容易擴展
- 更好的監控與分析

#### 🟢 **優先級 3：分環境設定**

**建議：**
- 區分開發環境（Development）、測試環境（Staging）、生產環境（Production）
- 開發環境可以放寬安全限制（例如：允許 localhost 無認證）
- 生產環境必須嚴格執行所有安全措施

**實作方式：**
- 使用環境變數區分環境（例如：`ENVIRONMENT=production`）
- 根據環境動態調整安全設定
- 生產環境強制要求認證，開發環境可選

#### 🟢 **優先級 4：加強日誌與審計**

**建議：**
- 記錄所有 API 呼叫（IP、時間、端點、請求內容、回應狀態）
- 記錄所有 WebSocket 連線與斷線
- 記錄所有 AI Provider API 呼叫（用於成本追蹤）
- 建立審計日誌系統

**實作方式：**
- 使用 FastAPI middleware 記錄所有請求
- 使用 structured logging（例如：JSON 格式）
- 整合日誌收集系統（例如：ELK Stack、Loki）

#### 🟢 **優先級 5：實作監控與告警**

**建議：**
- 監控 API 呼叫頻率
- 監控 WebSocket 連線數量
- 監控 AI Provider API 配額使用率
- 異常行為告警（例如：單一 IP 大量請求）

**實作方式：**
- 整合 Prometheus + Grafana
- 或使用商業監控服務（例如：Datadog、New Relic）
- 設定告警規則

#### 🟢 **優先級 6：IP 白名單 / 黑名單**

**建議：**
- 支援 IP 白名單（只允許特定 IP 存取）
- 支援 IP 黑名單（禁止特定 IP 存取）
- 自動封鎖可疑 IP

**實作方式：**
- 使用 FastAPI middleware 檢查 IP
- 維護 IP 白名單 / 黑名單資料表
- 或使用第三方服務（例如：Cloudflare、AWS WAF）

---

## 五、總結

### 5.1 風險摘要

**目前狀態：🔴 高風險**

- ❌ 所有 War Room endpoints **完全無認證保護**
- ❌ 任何人都可以無限制建立 session 並觸發 AI 分析
- ❌ 可能導致 API 配額耗盡與費用暴增
- ❌ 暴露系統內部狀態（活躍 sessions、providers）
- ⚠️ CORS 限制只在瀏覽器環境有效，無法防止直接 HTTP 呼叫

### 5.2 優先處理項目

**立即執行（1-2 天）：**
1. 加上基本 API Key 驗證
2. 限制或移除 Health Check 中的敏感資訊
3. 加入 Rate Limiting

**短期執行（1-2 週）：**
1. 統一 War Room 版本
2. 加入 Session 過期機制
3. 修正路由結構問題

**長期規劃（1-3 個月）：**
1. 實作完整的認證與授權系統
2. API Gateway 整合
3. 加強日誌與審計
4. 實作監控與告警

### 5.3 建議的最低安全標準

在部署到外網前，**至少**需要實作：

1. ✅ **API Key 驗證** - 所有端點都必須提供有效的 API Key
2. ✅ **Rate Limiting** - 限制每個 IP 的請求頻率
3. ✅ **移除敏感資訊** - Health Check 端點不應暴露內部狀態
4. ✅ **請求大小限制** - 防止資源耗盡攻擊
5. ✅ **日誌記錄** - 記錄所有 API 呼叫以便審計

**如果無法立即實作以上所有措施，強烈建議：**
- **不要將這些後端部署到外網**
- 僅在本機環境或內網環境使用
- 或者使用 VPN / 私有網路保護

---

**報告結束**

*本報告基於實際程式碼掃描生成，確保準確性與完整性。建議定期重新評估安全狀態。*

