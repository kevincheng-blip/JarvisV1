"""
環境變數載入器
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def load_env() -> None:
    """
    載入環境變數
    
    優先順序：
    1. 專案根目錄的 .env 檔案
    2. 系統環境變數
    """
    # 找到專案根目錄（JarvisV1）
    # 從當前檔案位置往上找，直到找到包含 .git 或 main.py 的目錄
    current_file = Path(__file__).resolve()
    # jgod/config/env_loader.py -> jgod/config -> jgod -> JarvisV1
    project_root = current_file.parent.parent.parent
    
    # 檢查是否找到專案根目錄
    if not (project_root / "main.py").exists() and not (project_root / ".git").exists():
        # 如果找不到，嘗試從當前工作目錄找
        cwd = Path.cwd()
        if (cwd / "main.py").exists() or (cwd / ".git").exists():
            project_root = cwd
    
    # 載入 .env 檔案
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=False)
    
    # 也嘗試載入當前目錄的 .env（作為 fallback）
    load_dotenv(override=False)


if __name__ == "__main__":
    # 測試用
    load_env()
    print("環境變數載入完成")
    print(f"OPENAI_API_KEY: {'已設定' if os.getenv('OPENAI_API_KEY') else '未設定'}")
    print(f"ANTHROPIC_API_KEY: {'已設定' if os.getenv('ANTHROPIC_API_KEY') else '未設定'}")
    print(f"GEMINI_API_KEY: {'已設定' if os.getenv('GEMINI_API_KEY') else '未設定'}")
    print(f"PERPLEXITY_API_KEY: {'已設定' if os.getenv('PERPLEXITY_API_KEY') else '未設定'}")
    print(f"FINMIND_TOKEN: {'已設定' if os.getenv('FINMIND_TOKEN') else '未設定'}")

