#!/bin/bash
# J-GOD Prediction Backfill - 一行命令版本
# 可直接複製貼上至 terminal 執行

cd /Users/kevincheng/JarvisV1 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-01-01" --end-date "2024-03-31" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-04-01" --end-date "2024-06-30" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-07-01" --end-date "2024-09-30" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "1301,1303,2308,2412" --start-date "2024-10-01" --end-date "2024-12-31" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "2303" --start-date "2024-07-18" --end-date "2024-09-30" && sleep 5 && PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols "2303" --start-date "2024-10-01" --end-date "2024-12-31"

