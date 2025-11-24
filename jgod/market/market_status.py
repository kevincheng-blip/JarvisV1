"""
市場狀態判斷：判斷台股/美股是否開盤
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pytz


class MarketStatus:
    """
    市場狀態判斷器
    
    功能：
    - 判斷台股是否開盤
    - 判斷美股是否開盤
    - 考慮時區和假日
    """
    
    # 台股時區
    TAIWAN_TZ = pytz.timezone("Asia/Taipei")
    # 美股時區（紐約）
    US_TZ = pytz.timezone("America/New_York")
    
    def __init__(self):
        """初始化市場狀態判斷器"""
        pass
    
    def is_taiwan_market_open(self, date: Optional[datetime] = None) -> bool:
        """
        判斷台股是否開盤
        
        Args:
            date: 要判斷的日期，如果為 None 則使用當前時間
        
        Returns:
            True 表示開盤，False 表示休市
        """
        if date is None:
            date = datetime.now(self.TAIWAN_TZ)
        elif date.tzinfo is None:
            date = self.TAIWAN_TZ.localize(date)
        else:
            date = date.astimezone(self.TAIWAN_TZ)
        
        # 檢查是否為週末
        weekday = date.weekday()  # 0=Monday, 6=Sunday
        if weekday >= 5:  # Saturday or Sunday
            return False
        
        # 檢查是否在交易時間內（9:00-13:30）
        hour = date.hour
        minute = date.minute
        
        # 早盤：9:00-11:30
        if 9 <= hour < 11 or (hour == 11 and minute <= 30):
            return True
        
        # 午盤：13:00-13:30
        if hour == 13 and minute <= 30:
            return True
        
        return False
    
    def is_us_market_open(self, date: Optional[datetime] = None) -> bool:
        """
        判斷美股是否開盤
        
        Args:
            date: 要判斷的日期，如果為 None 則使用當前時間
        
        Returns:
            True 表示開盤，False 表示休市
        """
        if date is None:
            date = datetime.now(self.US_TZ)
        elif date.tzinfo is None:
            date = self.US_TZ.localize(date)
        else:
            date = date.astimezone(self.US_TZ)
        
        # 檢查是否為週末
        weekday = date.weekday()
        if weekday >= 5:
            return False
        
        # 美股交易時間：9:30-16:00 ET
        hour = date.hour
        minute = date.minute
        
        if hour == 9 and minute >= 30:
            return True
        if 10 <= hour < 16:
            return True
        
        return False
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        取得當前市場狀態
        
        Returns:
            包含台股和美股狀態的字典
        """
        now = datetime.now()
        
        taiwan_open = self.is_taiwan_market_open()
        us_open = self.is_us_market_open()
        
        return {
            "timestamp": now.isoformat(),
            "taiwan": {
                "is_open": taiwan_open,
                "timezone": "Asia/Taipei",
            },
            "us": {
                "is_open": us_open,
                "timezone": "America/New_York",
            },
        }

