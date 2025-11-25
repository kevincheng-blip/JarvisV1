"""
Pytest 配置與共用 Fixtures
"""
import pytest
import os
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 載入環境變數
from jgod.config.env_loader import load_env
load_env()

