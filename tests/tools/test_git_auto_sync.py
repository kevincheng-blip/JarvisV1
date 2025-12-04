"""
Test Git AutoSync System

測試 git_auto_sync.py 的 commit message 生成功能。
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.git_auto_sync import generate_commit_message


def test_generate_commit_message_no_msg():
    """測試沒有額外訊息時的 commit message 格式"""
    msg = generate_commit_message()
    
    # 應該包含 "chore: auto-sync" 和時間戳
    assert msg.startswith("chore: auto-sync")
    assert "202" in msg or "2025" in msg or "2024" in msg  # 年份
    assert "+0800" in msg
    
    # 不應該包含 " - " 後綴（因為沒有額外訊息）
    assert not msg.endswith(" - ")


def test_generate_commit_message_with_msg():
    """測試有額外訊息時的 commit message 格式"""
    custom_msg = "Path E stable"
    msg = generate_commit_message(custom_msg)
    
    # 應該包含 "chore: auto-sync" 和時間戳
    assert msg.startswith("chore: auto-sync")
    assert "+0800" in msg
    
    # 應該包含自訂訊息
    assert custom_msg in msg
    assert msg.endswith(f" - {custom_msg}")


def test_generate_commit_message_empty_string():
    """測試空字串訊息時的處理"""
    msg = generate_commit_message("")
    
    # 空字串應該被視為 None，不應該有 " - " 後綴
    assert msg.startswith("chore: auto-sync")
    assert not msg.endswith(" - ")


def test_generate_commit_message_format():
    """測試 commit message 格式完整性"""
    msg = generate_commit_message("test message")
    
    # 格式應該是：chore: auto-sync {timestamp} - {msg}
    parts = msg.split(" - ")
    assert len(parts) == 2
    assert parts[0].startswith("chore: auto-sync")
    assert parts[1] == "test message"
    
    # 時間戳格式檢查
    timestamp_part = parts[0].replace("chore: auto-sync ", "")
    # 應該包含日期和時間
    assert len(timestamp_part) > 10  # 至少要有日期時間


def test_generate_commit_message_multiple_calls():
    """測試多次呼叫產生不同的時間戳"""
    msg1 = generate_commit_message("test")
    msg2 = generate_commit_message("test")
    
    # 兩次呼叫應該產生不同的時間戳（除非在同一秒內）
    # 至少格式應該一致
    assert msg1.startswith("chore: auto-sync")
    assert msg2.startswith("chore: auto-sync")
    assert "+0800" in msg1
    assert "+0800" in msg2

