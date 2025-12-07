#!/bin/bash
# J-GOD Prediction Backfill 批次腳本
# 目標：補齊 1301, 1303, 2308, 2412 的 2024 全年預測 + 2303 的 2024-07-18 ~ 2024-12-31 預測
# 執行方式：直接執行此腳本，或複製命令至 terminal

set -e  # 遇到錯誤立即停止

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== J-GOD Prediction Backfill 批次執行開始 ===${NC}"
echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 切換到專案根目錄
cd "$(dirname "$0")/.." || exit 1

# 定義要處理的股票
SYMBOLS_FULL_YEAR="1301,1303,2308,2412"
SYMBOL_PARTIAL="2303"

# ============================================================================
# 第一部分：補齊 4 檔股票的 2024 全年預測（按季度分批）
# ============================================================================

echo -e "${YELLOW}--- 第一部分：補齊 4 檔股票 2024 全年預測 ---${NC}"
echo "股票: ${SYMBOLS_FULL_YEAR}"
echo ""

# Q1: 2024-01-01 ~ 2024-03-31
echo -e "${GREEN}[批次 1/4] Q1 預測回填 (2024-01-01 ~ 2024-03-31)${NC}"
PYTHONPATH=. python scripts/run_backfill_predictions.py \
  --symbols "${SYMBOLS_FULL_YEAR}" \
  --start-date "2024-01-01" \
  --end-date "2024-03-31"
echo -e "${GREEN}✓ Q1 完成${NC}"
sleep 5

# Q2: 2024-04-01 ~ 2024-06-30
echo -e "${GREEN}[批次 2/4] Q2 預測回填 (2024-04-01 ~ 2024-06-30)${NC}"
PYTHONPATH=. python scripts/run_backfill_predictions.py \
  --symbols "${SYMBOLS_FULL_YEAR}" \
  --start-date "2024-04-01" \
  --end-date "2024-06-30"
echo -e "${GREEN}✓ Q2 完成${NC}"
sleep 5

# Q3: 2024-07-01 ~ 2024-09-30
echo -e "${GREEN}[批次 3/4] Q3 預測回填 (2024-07-01 ~ 2024-09-30)${NC}"
PYTHONPATH=. python scripts/run_backfill_predictions.py \
  --symbols "${SYMBOLS_FULL_YEAR}" \
  --start-date "2024-07-01" \
  --end-date "2024-09-30"
echo -e "${GREEN}✓ Q3 完成${NC}"
sleep 5

# Q4: 2024-10-01 ~ 2024-12-31
echo -e "${GREEN}[批次 4/4] Q4 預測回填 (2024-10-01 ~ 2024-12-31)${NC}"
PYTHONPATH=. python scripts/run_backfill_predictions.py \
  --symbols "${SYMBOLS_FULL_YEAR}" \
  --start-date "2024-10-01" \
  --end-date "2024-12-31"
echo -e "${GREEN}✓ Q4 完成${NC}"
sleep 5

# ============================================================================
# 第二部分：補齊 2303 從 2024-07-18 到 2024-12-31 的預測
# ============================================================================

echo ""
echo -e "${YELLOW}--- 第二部分：補齊 2303 的預測 (2024-07-18 ~ 2024-12-31) ---${NC}"
echo "股票: ${SYMBOL_PARTIAL}"
echo ""

# 2303 Q3 後半：2024-07-18 ~ 2024-09-30
echo -e "${GREEN}[批次 5/6] 2303 Q3 後半預測回填 (2024-07-18 ~ 2024-09-30)${NC}"
PYTHONPATH=. python scripts/run_backfill_predictions.py \
  --symbols "${SYMBOL_PARTIAL}" \
  --start-date "2024-07-18" \
  --end-date "2024-09-30"
echo -e "${GREEN}✓ 2303 Q3 後半完成${NC}"
sleep 5

# 2303 Q4：2024-10-01 ~ 2024-12-31
echo -e "${GREEN}[批次 6/6] 2303 Q4 預測回填 (2024-10-01 ~ 2024-12-31)${NC}"
PYTHONPATH=. python scripts/run_backfill_predictions.py \
  --symbols "${SYMBOL_PARTIAL}" \
  --start-date "2024-10-01" \
  --end-date "2024-12-31"
echo -e "${GREEN}✓ 2303 Q4 完成${NC}"

# ============================================================================
# 完成
# ============================================================================

echo ""
echo -e "${GREEN}=== 所有批次執行完成 ===${NC}"
echo "結束時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "執行總結："
echo "  - 已處理 4 檔股票（1301, 1303, 2308, 2412）的 2024 全年預測"
echo "  - 已處理 2303 的 2024-07-18 ~ 2024-12-31 預測"
echo ""
echo "建議檢查資料庫確認結果："
echo "  PYTHONPATH=. python -c \"import sqlite3; conn = sqlite3.connect('data/jgod_tw_stock.db'); cursor = conn.cursor(); cursor.execute('SELECT symbol, COUNT(*) FROM prediction_snapshots WHERE date >= \\\"2024-01-01\\\" AND date <= \\\"2024-12-31\\\" GROUP BY symbol ORDER BY symbol'); print('\\n'.join([f'{r[0]}: {r[1]} 筆' for r in cursor.fetchall()]))\""

