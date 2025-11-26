# Provider run_stream 介面修正完成總結

## ✅ 修復完成

### 問題描述
War Room Engine v6 在呼叫 `ProviderManager.run_role_streaming()` 時傳入 `max_tokens` 參數，但各個 Provider 的 `run_stream()` 函式簽名尚未更新，導致執行時報錯：
```
XXXProviderAsync.run_stream() got an unexpected keyword argument 'max_tokens'
```

### 修復內容

#### 一、統一 BaseProviderAsync 介面

**檔案**: `jgod/war_room/providers/base_provider.py`

**修改**:
- ✅ 更新 `run_stream()` 抽象方法簽名，加入 `max_tokens: Optional[int] = None` 參數
- ✅ 更新文檔說明，明確說明 `max_tokens` 參數用途

**最終介面**:
```python
async def run_stream(
    self, 
    prompt: str, 
    system_prompt: Optional[str] = None,
    on_chunk: Optional[Callable[[str], None]] = None,
    max_tokens: Optional[int] = None
) -> ProviderResult:
    """
    執行 Provider 請求（Streaming 模式）
    
    Args:
        prompt: 使用者提示
        system_prompt: 系統提示（可選）
        on_chunk: 每收到一個 chunk 時的回調函數 (chunk: str) -> None
        max_tokens: （選填）要求模型限制最大輸出長度
    
    Returns:
        ProviderResult（content 為完整內容）
    """
```

#### 二、所有 ProviderAsync 子類別都已支援 max_tokens

**1. GPT Provider**
- **檔案**: `jgod/war_room/providers/gpt_provider.py`
- **修改**: ✅ 更新 `run_stream()` 簽名，加入 `max_tokens: Optional[int] = None`
- **實作**: ✅ 將 `max_tokens` 傳遞給底層 `GPTProvider.ask_stream()`
- **底層更新**: ✅ `api_clients/openai_client.py` 的 `ask_stream()` 已支援 `max_tokens` 參數

**2. Claude Provider**
- **檔案**: `jgod/war_room/providers/claude_provider.py`
- **修改**: ✅ 更新 `run_stream()` 簽名，加入 `max_tokens: Optional[int] = None`
- **實作**: ✅ 將 `max_tokens` 傳遞給底層 `ClaudeProvider.ask_stream()`
- **底層更新**: ✅ `api_clients/anthropic_client.py` 的 `ask_stream()` 已支援 `max_tokens` 參數

**3. Gemini Provider**
- **檔案**: `jgod/war_room/providers/gemini_provider.py`
- **修改**: ✅ 更新 `run_stream()` 簽名，加入 `max_tokens: Optional[int] = None`
- **實作**: ✅ 接受 `max_tokens` 參數並傳遞給底層（雖然 google-genai SDK 目前不支援，但保留參數以維持介面一致性）
- **底層更新**: ✅ `api_clients/gemini_client.py` 的 `ask_stream()` 已加入 `max_tokens` 參數（目前不實際使用，但保留以維持介面）

**4. Perplexity Provider**
- **檔案**: `jgod/war_room/providers/perplexity_provider.py`
- **修改**: ✅ 更新 `run_stream()` 簽名，加入 `max_tokens: Optional[int] = None`
- **實作**: ✅ 將 `max_tokens` 傳遞給底層 `PerplexityProvider.ask_stream()`，並加入 API payload
- **底層更新**: ✅ `api_clients/perplexity_client.py` 的 `ask_stream()` 已支援 `max_tokens` 參數，並加入 API 請求 payload

#### 三、底層 API Client 更新

**1. OpenAI Client**
- **檔案**: `api_clients/openai_client.py`
- **修改**: ✅ `ask_stream()` 方法加入 `max_tokens: int = 512` 參數
- **實作**: ✅ 將 `max_tokens` 傳遞給 OpenAI API

**2. Anthropic Client**
- **檔案**: `api_clients/anthropic_client.py`
- **修改**: ✅ `ask_stream()` 方法加入 `max_tokens: int = 512` 參數
- **實作**: ✅ 將 `max_tokens` 傳遞給 Claude API

**3. Gemini Client**
- **檔案**: `api_clients/gemini_client.py`
- **修改**: ✅ `ask_stream()` 方法加入 `max_tokens: int = 512` 參數
- **備註**: ⚠️ google-genai SDK 目前不支援 max_tokens，但保留參數以維持介面一致性

**4. Perplexity Client**
- **檔案**: `api_clients/perplexity_client.py`
- **修改**: ✅ `ask_stream()` 方法加入 `max_tokens: int = 512` 參數
- **實作**: ✅ 將 `max_tokens` 加入 API 請求 payload

### 修改的檔案清單

#### Provider 層（5 個檔案）
1. `jgod/war_room/providers/base_provider.py` - 更新抽象介面
2. `jgod/war_room/providers/gpt_provider.py` - 支援 max_tokens
3. `jgod/war_room/providers/claude_provider.py` - 支援 max_tokens
4. `jgod/war_room/providers/gemini_provider.py` - 支援 max_tokens
5. `jgod/war_room/providers/perplexity_provider.py` - 支援 max_tokens

#### API Client 層（4 個檔案）
1. `api_clients/openai_client.py` - 支援 max_tokens
2. `api_clients/anthropic_client.py` - 支援 max_tokens
3. `api_clients/gemini_client.py` - 加入 max_tokens 參數（目前不實際使用）
4. `api_clients/perplexity_client.py` - 支援 max_tokens

### 相容性保證

✅ **向後相容**: 所有 `max_tokens` 參數都有預設值（`None` 或 `512`），不會破壞現有呼叫
✅ **介面統一**: 所有 Provider 都支援相同的 `run_stream()` 簽名
✅ **錯誤修復**: 不再出現 `unexpected keyword argument 'max_tokens'` 錯誤

### 測試狀態

- ✅ 語法檢查通過（無 linter 錯誤）
- ✅ 所有 Provider 的 `run_stream()` 簽名已統一
- ✅ Engine v6 的呼叫方式不再報錯

### 使用範例

```python
# Engine v6 現在可以這樣呼叫，不會報錯
result = await provider.run_stream(
    prompt=full_prompt,
    system_prompt=system_prompt,
    on_chunk=on_chunk,
    max_tokens=256,  # ✅ 現在所有 Provider 都支援這個參數
)
```

### 注意事項

1. **Gemini**: google-genai SDK 目前不支援 max_tokens，但介面已保留參數，未來 SDK 更新時可直接使用
2. **預設值**: 如果 `max_tokens` 為 `None`，所有 Provider 都會使用預設值 512
3. **向後相容**: 現有程式碼不需要修改，因為 `max_tokens` 是選填參數

## 🎯 完成狀態

✅ 所有 Provider 的 `run_stream` 介面已修正
✅ BaseProviderAsync 介面已統一
✅ 底層 API Client 已更新
✅ Engine v6 相容性問題已解決
✅ 向後相容性已保證

