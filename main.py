#!/usr/bin/env python3
"""
Zeabur 入口點：啟動 Streamlit 應用程式
"""
import os
import sys
import subprocess


def main():
    """啟動 Streamlit 應用程式"""
    # 讀取環境變數 PORT，如果沒有就預設用 8000
    port = os.getenv("PORT", "8000")
    
    # Streamlit 應用程式路徑
    app_path = "jgod/war_room/war_room_app.py"
    
    # 建立 streamlit 命令
    cmd = [
        sys.executable,  # 使用當前 Python 解釋器
        "-m", "streamlit", "run",
        app_path,
        "--server.port", port,
        "--server.address", "0.0.0.0"
    ]
    
    # 執行 streamlit 命令
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n應用程式已停止")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"錯誤：無法啟動 Streamlit 應用程式: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

