# War Room Frontend v6 PRO - 角色 Key 映射修復總結

## ✅ 修復完成

### 問題描述
只有 Strategist 角色卡片有內容，其他角色（Intel Officer, Scout, Risk Officer, Quant Lead, Execution Officer）卡片沒有顯示文字。

**根本原因**：
- 後端發送的 `event.role` 是 "Intel Officer" 這種格式（後端名稱）
- 前端期望的是 "intel_officer" 這種格式（前端 RoleKey）
- 當處理事件時，`newState.roles[event.role as RoleKey]` 找不到對應的角色，因為 key 不匹配

### 修復方案

#### 1. 建立統一的角色映射表

**檔案**: `frontend/war-room-web/lib/types/warRoom.ts`

新增 `ROLE_NAME_MAP` 和 `resolveRoleKeyFromBackendName()` 函式：

```typescript
// 統一的角色映射表（後端名稱 → 前端 RoleKey）
export const ROLE_NAME_MAP: Record<RoleKey, { backendName: string; labelZh: string; labelEn: string }> = {
  intel_officer: { backendName: "Intel Officer", labelZh: "情報官", labelEn: "Intel Officer" },
  scout: { backendName: "Scout", labelZh: "斥候官", labelEn: "Scout" },
  risk_officer: { backendName: "Risk Officer", labelZh: "風控官", labelEn: "Risk Officer" },
  quant_lead: { backendName: "Quant Lead", labelZh: "量化官", labelEn: "Quant Lead" },
  strategist: { backendName: "Strategist", labelZh: "策略官", labelEn: "Strategist" },
  execution_officer: { backendName: "Execution Officer", labelZh: "執行官", labelEn: "Execution Officer" },
};

/**
 * 從後端角色名稱解析為前端 RoleKey
 * @param name 後端發送的角色名稱（例如 "Intel Officer"）
 * @returns 對應的 RoleKey，如果找不到則返回 null
 */
export function resolveRoleKeyFromBackendName(name: string | null | undefined): RoleKey | null {
  if (!name) return null;
  
  const entry = Object.entries(ROLE_NAME_MAP).find(([, v]) => v.backendName === name);
  return entry ? (entry[0] as RoleKey) : null;
}
```

#### 2. 修改事件處理邏輯

**檔案**: 
- `frontend/war-room-web/app/page.tsx`
- `frontend/war-room-web/app/demo/tsmc/page.tsx`

在 `handleEvent` 函式中：
- 使用 `resolveRoleKeyFromBackendName(event.role)` 解析後端角色名稱
- 所有角色相關的事件處理都使用解析後的 `resolvedRoleKey`
- 添加 debug log（開發模式）和警告訊息

**修改前**:
```typescript
case "role_chunk":
  if (event.role && event.chunk) {
    const role = newState.roles[event.role as RoleKey]; // ❌ 錯誤：event.role 是 "Intel Officer"，不是 "intel_officer"
    if (role) {
      role.content += event.chunk;
    }
  }
  break;
```

**修改後**:
```typescript
// 解析後端角色名稱為前端 RoleKey
const resolvedRoleKey = event.role ? resolveRoleKeyFromBackendName(event.role) : null;

// Debug log（開發模式）
if (process.env.NODE_ENV === "development") {
  console.debug("[WS_EVENT]", event.type, event.role, resolvedRoleKey, resolvedRoleKey ? newState.roles[resolvedRoleKey] : null);
}

// 如果無法解析角色名稱，發出警告
if (event.role && !resolvedRoleKey) {
  console.warn(`[WS_EVENT] Unknown role name from backend: "${event.role}"`);
}

case "role_chunk":
  if (resolvedRoleKey && event.chunk) {
    const role = newState.roles[resolvedRoleKey]; // ✅ 正確：使用解析後的 RoleKey
    if (role) {
      role.content += event.chunk;
      role.status = "running";
    }
  }
  break;
```

#### 3. 統一組件使用 RoleKey

**檔案**:
- `frontend/war-room-web/components/pro/RoleCardPro.tsx`
- `frontend/war-room-web/components/war-room/RoleGrid.tsx`
- `frontend/war-room-web/components/war-room/MissionSummary.tsx`
- `frontend/war-room-web/components/pro/SummaryCardPro.tsx`

所有組件都使用 `ROLE_NAME_MAP` 來取得角色顯示名稱，並使用 `RoleKey` 作為 state 的 key。

**RoleCardPro.tsx**:
```typescript
import { RoleState, ROLE_NAME_MAP } from "@/lib/types/warRoom";

// 使用 ROLE_NAME_MAP 取得顯示名稱
<span className="bg-gradient-to-r from-ai-blue to-military-green bg-clip-text text-transparent">
  {ROLE_NAME_MAP[role.key]?.labelZh || role.key}
</span>
<span className="text-xs text-gray-500">
  {ROLE_NAME_MAP[role.key]?.labelEn || role.key}
</span>
```

**MissionSummary.tsx**:
```typescript
// 使用 RoleKey 而不是後端名稱
const strategist = state.roles["strategist"]; // ✅ 正確
const riskOfficer = state.roles["risk_officer"]; // ✅ 正確
const quantLead = state.roles["quant_lead"]; // ✅ 正確
```

### 修改的檔案

1. **`frontend/war-room-web/lib/types/warRoom.ts`**
   - 新增 `ROLE_NAME_MAP` 映射表
   - 新增 `resolveRoleKeyFromBackendName()` 函式
   - 修改 `WarRoomEvent` 介面，`role` 欄位改為 `string | null`（因為後端發送的是字串）

2. **`frontend/war-room-web/app/page.tsx`**
   - 修改 `handleEvent` 函式，使用 `resolveRoleKeyFromBackendName()` 解析角色名稱
   - 添加 debug log 和警告訊息

3. **`frontend/war-room-web/app/demo/tsmc/page.tsx`**
   - 修改 `handleEvent` 函式，使用 `resolveRoleKeyFromBackendName()` 解析角色名稱
   - 添加 debug log 和警告訊息

4. **`frontend/war-room-web/components/pro/RoleCardPro.tsx`**
   - 改用 `ROLE_NAME_MAP` 取得角色顯示名稱

5. **`frontend/war-room-web/components/war-room/RoleGrid.tsx`**
   - 添加角色存在性檢查和警告

6. **`frontend/war-room-web/components/war-room/MissionSummary.tsx`**
   - 修正角色 key，使用 `RoleKey` 而不是後端名稱

### 預期行為

**修復前**:
- ❌ 只有 Strategist 角色卡片有內容
- ❌ 其他角色（Intel Officer, Scout, Risk Officer, Quant Lead, Execution Officer）卡片沒有顯示文字
- ❌ 事件處理時找不到對應的角色 state

**修復後**:
- ✅ 所有角色卡片都能正確顯示內容
- ✅ 後端發送的 "Intel Officer" 等名稱能正確映射到前端的 "intel_officer" 等 RoleKey
- ✅ 開發模式下可以在 console 看到詳細的 debug log
- ✅ 如果後端發送未知的角色名稱，會在 console 顯示警告

### 測試狀態

- ✅ TypeScript 編譯通過
- ✅ Next.js build 成功
- ✅ 無 linter 錯誤

### 使用方式

1. **開發模式 Debug Log**:
   - 在瀏覽器 console 中可以看到 `[WS_EVENT]` 開頭的 debug log
   - 格式：`[WS_EVENT] <event_type> <backend_role_name> <resolved_role_key> <role_state>`

2. **角色映射**:
   - 後端發送 "Intel Officer" → 前端解析為 "intel_officer"
   - 後端發送 "Scout" → 前端解析為 "scout"
   - 後端發送 "Risk Officer" → 前端解析為 "risk_officer"
   - 後端發送 "Quant Lead" → 前端解析為 "quant_lead"
   - 後端發送 "Strategist" → 前端解析為 "strategist"
   - 後端發送 "Execution Officer" → 前端解析為 "execution_officer"

3. **錯誤處理**:
   - 如果後端發送未知的角色名稱，會在 console 顯示警告
   - 不會靜默丟掉事件，但也不會更新錯誤的角色 state

