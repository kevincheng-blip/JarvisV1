# Ultra Auto-Git Mode - 永久自動 Git 管理模式

## 📋 概述

Ultra Auto-Git Mode 是一個完全自動化的 Git 管理系統，無需任何手動操作即可：
- 自動偵測變更並 commit + push
- 產生專業的 commit message
- 每日自動建立版本 tag (vYYYY.MM.DD)
- 每日自動產生 Release Notes
- 自動處理衝突

## 🚀 快速開始

### 1. 系統已自動啟動

Ultra Auto-Git Mode 已經啟動並完成第一次 commit + push。你不需要做任何操作。

### 2. 每日自動執行（可選）

如果你想設定每日 23:59 自動執行每日任務（tag + release notes），執行：

```bash
bash scripts/setup_ultra_git_cron.sh
```

這會設定一個 cron job，每天 23:59 自動執行：
- 建立每日版本 tag
- 產生每日 Release Notes

### 3. 手動觸發（如果需要）

```bash
# 執行完整流程（檢查變更 → commit → push → 每日任務）
python3 scripts/ultra_auto_git.py

# 只執行每日任務（tag + release notes）
python3 scripts/ultra_auto_git.py --daily-only
```

## 📁 檔案結構

```
scripts/
├── ultra_auto_git.py          # 核心自動化腳本
├── ultra_git_hook.py          # Hook 包裝器（供 IDE/工具使用）
└── setup_ultra_git_cron.sh    # Cron job 設定腳本

release_notes/
└── release_YYYY_MM_DD.md       # 每日 Release Notes（自動產生）
```

## 🔄 工作流程

### 自動 Commit + Push 流程

1. **偵測變更**
   - 自動掃描所有檔案變更
   - 排除 .gitignore 中的檔案

2. **更新 .gitignore**
   - 自動確保 .gitignore 包含所有必要規則
   - 如果缺少規則會自動補上

3. **分析變更**
   - 分類檔案（新增/修改/刪除/重新命名）
   - 偵測影響的模組（Path A, Alpha Engine, Risk Model, etc.）

4. **產生 Commit Message**
   - Summary line (<= 50 chars)
   - Details: What changed
   - Why it was changed
   - Impact on the system
   - Related modules

5. **Stage + Commit**
   - 自動 stage 所有變更
   - 自動 commit（使用專業 message）

6. **Push**
   - 自動 push 到 origin/main
   - 如果遇到衝突，自動執行 `git pull --rebase`
   - 如果仍有衝突，以本地版本為主自動解決

### 每日任務流程（23:59 執行）

1. **建立每日 Tag**
   - 格式：`vYYYY.MM.DD`（例如：`v2025.12.02`）
   - 自動 push tag 到 remote

2. **產生 Release Notes**
   - 檔案：`release_notes/release_YYYY_MM_DD.md`
   - 內容包含：
     - 今日所有 commit 摘要
     - 程式碼統計（新增/刪除行數）
     - 影響的模組
     - 變更的檔案清單
     - 重大更新
     - 待辦事項

## 📝 Commit Message 格式

```
<summary line (<= 50 chars)>

Details:

What changed
- Added X file(s): ...
- Modified X file(s): ...
- Deleted X file(s): ...

Why it was changed
- Automated commit from Ultra Auto-Git Mode
- Code changes detected and committed automatically

Impact on the system
- Path A: Backtest pipeline or data loading updates
- Alpha Engine: Signal generation or factor computation changes
- ...

Related modules: Path A, Alpha Engine, Risk Model
```

## 🎯 功能特點

### ✅ 完全自動化
- 不需要任何手動操作
- 不需要確認 commit message
- 不需要確認 push
- 不需要選擇檔案

### ✅ 智能衝突處理
- 自動執行 `git pull --rebase`
- 如果仍有衝突，以本地版本為主
- 自動重新 push

### ✅ 專業 Commit Message
- 自動分析變更內容
- 自動偵測影響的模組
- 包含 What/Why/Impact/Related modules

### ✅ 每日版本管理
- 每日自動建立 tag
- 每日自動產生 Release Notes
- 完整的變更追蹤

## 🚫 嚴禁事項

系統**不會**：
- ❌ 詢問 commit message
- ❌ 詢問要不要 push
- ❌ 停在 pending changes
- ❌ 要求選擇哪些檔案要 commit
- ❌ 自動重寫程式碼（除非你要求）

## 📊 範例輸出

### Commit Message 範例

```
Add Path A experiment runner script

Details:

What changed
- Added 1 file(s): run_path_a_experiment.py
- Modified 1 file(s): .gitignore

Why it was changed
- Automated commit from Ultra Auto-Git Mode
- Code changes detected and committed automatically

Impact on the system
- Path A: Backtest pipeline or data loading updates

Related modules: Path A
```

### Release Notes 範例

見 `release_notes/release_2025_12_02.md`

## 🔧 設定與自訂

### 修改 .gitignore 規則

編輯 `scripts/ultra_auto_git.py` 中的 `ensure_gitignore()` 函數。

### 修改 Commit Message 格式

編輯 `scripts/ultra_auto_git.py` 中的 `generate_commit_message()` 函數。

### 修改 Release Notes 格式

編輯 `scripts/ultra_auto_git.py` 中的 `generate_daily_release_notes()` 函數。

## 📞 故障排除

### 如果 Push 失敗

系統會自動嘗試：
1. `git pull --rebase`
2. 如果仍有衝突，以本地版本為主
3. 重新 push

如果仍然失敗，會輸出錯誤訊息，但不會卡住。

### 如果 Cron Job 沒有執行

檢查 cron job：
```bash
crontab -l
```

重新設定：
```bash
bash scripts/setup_ultra_git_cron.sh
```

### 查看日誌

每日任務的日誌會寫入：
```
logs/ultra_git_daily.log
```

## 🎉 使用體驗

啟動 Ultra Auto-Git Mode 後：

✅ VSCode 不會再出現「15 個變更要提交」  
✅ 不會再看到「還需要 commit」  
✅ 不需要手動 push、pull、merge  
✅ 每天會多一個 `release_notes/release_YYYY_MM_DD.md`  
✅ Git 狀態永遠是乾淨、同步、無衝突  
✅ Cursor 會變成自動 Git 工程師  

## 📚 相關文件

- [Path A Standard](./J-GOD_PATH_A_STANDARD_v1.md)
- [FinMind Loader Standard](./J-GOD_FINMIND_LOADER_STANDARD_v1.md)
- [System Progress Summary](./JGOD_SYSTEM_PROGRESS_SUMMARY.md)

---

*Ultra Auto-Git Mode v1.0 - 永久自動 Git 管理模式*

