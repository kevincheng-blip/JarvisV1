"""
J-GOD: Jarvis Global Optimizer & Decision Engine

Main package for J-GOD trading system.
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip (will rely on system environment)
    pass

__version__ = "1.0.0"

