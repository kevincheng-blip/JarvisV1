"""
AI 訊號橋接器：將 AI 建議轉換為交易訊號
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

from .base_strategy import BaseStrategy, Signal, SignalType
from api_clients.openai_client import GPTProvider
from api_clients.anthropic_client import ClaudeProvider
from api_clients.gemini_client import GeminiProvider


class AISignalBridge(BaseStrategy):
    """
    AI 訊號橋接器
    
    功能：
    - 接受 AI 提供者的多空建議
    - 將建議轉換為標準化交易訊號
    - 支援多個 AI 提供者
    """
    
    def __init__(self, provider: str = "gpt"):
        """
        初始化 AI 訊號橋接器
        
        Args:
            provider: AI 提供者名稱（gpt, claude, gemini）
        """
        super().__init__(f"AI訊號橋接器({provider})")
        self.provider_name = provider
        self._provider = self._get_provider(provider)
    
    def _get_provider(self, name: str):
        """取得 AI 提供者實例"""
        name = name.lower()
        if name in ["gpt", "openai"]:
            return GPTProvider()
        elif name == "claude":
            return ClaudeProvider()
        elif name == "gemini":
            return GeminiProvider()
        else:
            return GPTProvider()  # 預設使用 GPT
    
    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        current_price: Optional[float] = None,
        question: Optional[str] = None,
    ) -> Optional[Signal]:
        """
        產生交易訊號（基於 AI 建議）
        
        Args:
            symbol: 股票代號
            data: 歷史價格資料
            current_price: 當前價格
            question: 要問 AI 的問題（如果為 None 則使用預設問題）
        
        Returns:
            交易訊號
        """
        if not self.validate_data(data):
            return None
        
        price = current_price if current_price is not None else self.get_current_price(data)
        
        # 準備給 AI 的資料摘要
        if len(data) >= 5:
            recent_data = data.tail(5)
            price_summary = f"近5日收盤價: {', '.join([f'{p:.2f}' for p in recent_data['close'].tolist()])}"
        else:
            price_summary = f"當前價格: {price:.2f}"
        
        # 準備問題
        if question is None:
            question = f"根據 {symbol} 的當前價格 {price:.2f} 和近期走勢，你建議買入、賣出還是持有？請簡短回答（買入/賣出/持有）並說明原因。"
        
        system_prompt = """
        你是一個專業的股票分析師。請根據提供的資料給出交易建議。
        回答格式：第一行是建議（買入/賣出/持有），第二行是簡短原因。
        """
        
        user_prompt = f"""
        股票代號：{symbol}
        當前價格：{price:.2f}
        {price_summary}
        
        問題：{question}
        """
        
        try:
            response = self._provider.ask(system_prompt, user_prompt)
            if not response:
                return None
            
            # 解析 AI 回應
            lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
            if not lines:
                return None
            
            first_line = lines[0].lower()
            signal_type = SignalType.HOLD
            confidence = 0.5
            
            if "買入" in first_line or "buy" in first_line or "多" in first_line:
                signal_type = SignalType.BUY
                confidence = 0.7
            elif "賣出" in first_line or "sell" in first_line or "空" in first_line:
                signal_type = SignalType.SELL
                confidence = 0.7
            
            reason = "\n".join(lines[1:3]) if len(lines) > 1 else lines[0]
            
            return Signal(
                signal_type=signal_type,
                symbol=symbol,
                timestamp=datetime.now(),
                price=price,
                confidence=confidence,
                reason=reason,
                metadata={"provider": self.provider_name, "raw_response": response},
            )
        except Exception as e:
            print(f"AI 訊號橋接器錯誤：{e}")
            return None

