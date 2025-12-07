# J-GOD Prediction Backfill 批次指令

**生成時間：** 2025-01-06  
**目標：** 補齊 1301, 1303, 2308, 2412 的 2024 全年預測 + 2303 的 2024-07-18 ~ 2024-12-31 預測

---

## 方式一：直接執行批次腳本（推薦）

```bash
cd /Users/kevincheng/JarvisV1
bash scripts/backfill_predictions_batch.sh
```

---

## 方式二：手動執行批次命令（可逐步執行）

### 第一部分：補齊 4 檔股票的 2024 全年預測

```bash
# 切換到專案根目錄
cd /Users/kevincheng/JarvisV1

# [批次 1/4] Q1: 2024-01-01 ~ 2024-03-31
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-01-01" --end-date "2024-03-31"
sleep 5

# [批次 2/4] Q2: 2024-04-01 ~ 2024-06-30
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-04-01" --end-date "2024-06-30"
sleep 5

# [批次 3/4] Q3: 2024-07-01 ~ 2024-09-30
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-07-01" --end-date "2024-09-30"
sleep 5

# [批次 4/4] Q4: 2024-10-01 ~ 2024-12-31
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-10-01" --end-date "2024-12-31"
sleep 5
```

### 第二部分：補齊 2303 從 2024-07-18 到 2024-12-31 的預測

```bash
# [批次 5/6] 2303 Q3 後半: 2024-07-18 ~ 2024-09-30
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "2303" --start-date "2024-07-18" --end-date "2024-09-30"
sleep 5

# [批次 6/6] 2303 Q4: 2024-10-01 ~ 2024-12-31
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "2303" --start-date "2024-10-01" --end-date "2024-12-31"
```

---

## 方式三：一行命令執行所有批次（複製全部）

```bash
cd /Users/kevincheng/JarvisV1 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-01-01" --end-date "2024-03-31" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-04-01" --end-date "2024-06-30" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-07-01" --end-date "2024-09-30" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-10-01" --end-date "2024-12-31" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "2303" --start-date "2024-07-18" --end-date "2024-09-30" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "2303" --start-date "2024-10-01" --end-date "2024-12-31"
```

---

## 執行後驗證

執行完成後，可以用以下命令檢查結果：

```bash
cd /Users/kevincheng/JarvisV1
python3 -c "
import sqlite3
from pathlib import Path

db_path = Path('data/jgod_tw_stock.db')
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('=== 2024 預測資料統計 ===')
    cursor.execute('''
        SELECT symbol, COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date
        FROM prediction_snapshots
        WHERE date >= '2024-01-01' AND date <= '2024-12-31'
        GROUP BY symbol
        ORDER BY symbol
    ''')
    
    for row in cursor.fetchall():
        symbol, count, min_date, max_date = row
        print(f'{symbol}: {count} 筆 ({min_date} ~ {max_date})')
    
    conn.close()
"
```

---

## 注意事項

1. **預測腳本會自動跳過已存在的預測**（除非使用 `--force`），所以可以安全地重複執行
2. **每批之間會 sleep 5 秒**，避免資料庫鎖定
3. **預測回填不直接呼叫 FinMind API**，而是從資料庫讀取 indicator_snapshots，所以不需要擔心 API 限制
4. **如果某個日期沒有 indicator_snapshots**，該日期會被自動跳過

---

## 預期結果

執行完成後，預期應該有：

- **1301**: 約 366 筆預測（2024-01-01 ~ 2024-12-31）
- **1303**: 約 366 筆預測（2024-01-01 ~ 2024-12-31）
- **2303**: 約 310 筆預測（2024-01-01 ~ 2024-12-31，包含原有的 143 筆）
- **2308**: 約 366 筆預測（2024-01-01 ~ 2024-12-31）
- **2412**: 約 366 筆預測（2024-01-01 ~ 2024-12-31）

（實際筆數可能會因為缺少某些交易日的 indicator_snapshots 而略少）

