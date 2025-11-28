"""
信息時間引擎（F_InfoTime）：Volume Bar 生成器

本模組實作創世紀量化系統 Step 2：信息時間引擎。

核心功能：
1. VolumeBar 資料結構：定義 Volume Bar 的標準格式
2. InfoTimeBarGenerator：累積 Tick 數據，形成 Volume Bar
3. VWAP 計算：Volume Weighted Average Price
4. F_InfoTime 因子計算：current_interval / long_term_avg_freq

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from dataclasses import dataclass, field
from typing import Optional, List, Deque
from collections import deque
import time

from data_feed.tick_handler import UnifiedTick


# ============================================================================
# VolumeBar 資料結構定義
# ============================================================================

@dataclass
class VolumeBar:
    """
    Volume Bar 資料結構
    
    Volume Bar 是基於累積成交量形成的時間單位，而非時鐘時間。
    當累積成交量達到 K_VOLUME_BAR_SIZE（預設 5M）時，形成一個 Volume Bar。
    
    Attributes:
        start_ts: Volume Bar 開始時間戳（第一個 Tick 的時間）
        end_ts: Volume Bar 結束時間戳（最後一個 Tick 的時間）
        symbol: 股票代號
        vwap: Volume Weighted Average Price（成交量加權平均價格）
        total_volume: 累積成交量
        tick_count: 包含的 Tick 數量
        open_price: 開盤價（第一個 Tick 的價格）
        high_price: 最高價
        low_price: 最低價
        close_price: 收盤價（最後一個 Tick 的價格）
        avg_bid: 平均買價
        avg_ask: 平均賣價
    """
    start_ts: float
    end_ts: float
    symbol: str
    vwap: float
    total_volume: int
    tick_count: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    avg_bid: float
    avg_ask: float
    
    def __post_init__(self):
        """驗證數據完整性"""
        if self.start_ts > self.end_ts:
            raise ValueError(f"Invalid time range: start_ts={self.start_ts}, end_ts={self.end_ts}")
        if self.vwap <= 0:
            raise ValueError(f"Invalid VWAP: {self.vwap}")
        if self.total_volume <= 0:
            raise ValueError(f"Invalid total_volume: {self.total_volume}")
        if self.high_price < self.low_price:
            raise ValueError(f"Invalid price range: high={self.high_price}, low={self.low_price}")


# ============================================================================
# InfoTimeBarGenerator：Volume Bar 生成器
# ============================================================================

class InfoTimeBarGenerator:
    """
    信息時間 Volume Bar 生成器
    
    功能：
    1. 累積 UnifiedTick 數據
    2. 當累積成交量達到 K_VOLUME_BAR_SIZE 時，產生一個 VolumeBar
    3. 計算 VWAP（Volume Weighted Average Price）
    4. 追蹤 Volume Bar 事件序列（用於後續 F_Inertia、F_PT、F_MRR 等因子）
    
    核心參數：
    - K_VOLUME_BAR_SIZE: 每個 Volume Bar 的目標成交量（預設 5,000,000）
    """
    
    # 每個 Volume Bar 的目標成交量（5M = 5,000,000）
    K_VOLUME_BAR_SIZE: int = 5_000_000
    
    def __init__(self, volume_bar_size: int = None):
        """
        初始化 Volume Bar 生成器
        
        Args:
            volume_bar_size: 每個 Volume Bar 的目標成交量（預設使用 K_VOLUME_BAR_SIZE）
        """
        self.volume_bar_size = volume_bar_size or self.K_VOLUME_BAR_SIZE
        
        # 當前 Volume Bar 的累積數據
        self.current_bar_ticks: List[UnifiedTick] = []
        self.current_bar_volume: int = 0
        self.current_bar_price_volume_sum: float = 0.0  # 用於計算 VWAP
        self.current_bar_start_ts: Optional[float] = None
        self.current_symbol: Optional[str] = None
        
        # 已完成的 Volume Bar 歷史（用於計算 F_InfoTime）
        self.completed_bars: Deque[VolumeBar] = deque(maxlen=100)  # 保留最近 100 個 Bar
        
        # 統計資訊（用於 F_InfoTime 計算）
        self.bar_intervals: Deque[float] = deque(maxlen=20)  # 保留最近 20 個 Bar 的間隔時間
    
    def add_tick(self, tick: UnifiedTick) -> Optional[VolumeBar]:
        """
        新增一個 Tick，累積 Volume，當達到目標成交量時產生 VolumeBar
        
        Args:
            tick: UnifiedTick 數據
        
        Returns:
            VolumeBar: 當累積成交量達到目標時，回傳完成的 VolumeBar；否則回傳 None
        """
        # 驗證 Tick 數據
        if tick.volume <= 0:
            return None  # 忽略無成交量的 Tick
        
        # 如果是新的 Volume Bar（第一個 Tick 或 symbol 改變）
        if self.current_bar_start_ts is None or self.current_symbol != tick.symbol:
            self._start_new_bar(tick)
        
        # 累積當前 Volume Bar 的數據
        self.current_bar_ticks.append(tick)
        self.current_bar_volume += tick.volume
        self.current_bar_price_volume_sum += tick.price * tick.volume
        
        # 更新結束時間戳
        self.current_bar_end_ts = tick.timestamp
        
        # 檢查是否達到目標成交量
        if self.current_bar_volume >= self.volume_bar_size:
            # 產生完整的 VolumeBar
            volume_bar = self._create_volume_bar()
            
            # 重置當前 Bar 狀態
            self._start_new_bar(tick)
            
            return volume_bar
        
        return None
    
    def _start_new_bar(self, tick: UnifiedTick):
        """
        開始一個新的 Volume Bar
        
        Args:
            tick: 第一個 Tick（用於初始化）
        """
        self.current_bar_ticks = [tick]
        self.current_bar_volume = tick.volume
        self.current_bar_price_volume_sum = tick.price * tick.volume
        self.current_bar_start_ts = tick.timestamp
        self.current_bar_end_ts = tick.timestamp
        self.current_symbol = tick.symbol
    
    def _create_volume_bar(self) -> VolumeBar:
        """
        從當前累積的 Tick 數據建立 VolumeBar
        
        Returns:
            VolumeBar: 完整的 Volume Bar 數據
        """
        if not self.current_bar_ticks:
            raise ValueError("Cannot create VolumeBar: no ticks accumulated")
        
        # 計算 VWAP
        vwap = self.current_bar_price_volume_sum / self.current_bar_volume if self.current_bar_volume > 0 else 0.0
        
        # 計算價格範圍
        prices = [tick.price for tick in self.current_bar_ticks]
        open_price = self.current_bar_ticks[0].price
        close_price = self.current_bar_ticks[-1].price
        high_price = max(prices)
        low_price = min(prices)
        
        # 計算平均買賣價
        avg_bid = sum(tick.bid_price for tick in self.current_bar_ticks) / len(self.current_bar_ticks)
        avg_ask = sum(tick.ask_price for tick in self.current_bar_ticks) / len(self.current_bar_ticks)
        
        # 建立 VolumeBar（確保時間順序正確）
        # 使用 min/max 確保時間順序，不依賴列表順序
        timestamps = [tick.timestamp for tick in self.current_bar_ticks]
        start_ts = min(timestamps)
        end_ts = max(timestamps)
        
        volume_bar = VolumeBar(
            start_ts=start_ts,
            end_ts=end_ts,
            symbol=self.current_symbol,
            vwap=vwap,
            total_volume=self.current_bar_volume,
            tick_count=len(self.current_bar_ticks),
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            avg_bid=avg_bid,
            avg_ask=avg_ask,
        )
        
        # 記錄到歷史
        self.completed_bars.append(volume_bar)
        
        # 計算 Bar 間隔時間（用於 F_InfoTime）
        if len(self.completed_bars) >= 2:
            interval = volume_bar.end_ts - self.completed_bars[-2].end_ts
            self.bar_intervals.append(interval)
        
        return volume_bar
    
    def get_current_bar_progress(self) -> dict:
        """
        取得當前 Volume Bar 的進度資訊
        
        Returns:
            dict: 包含當前 Bar 的進度資訊
        """
        if self.current_bar_start_ts is None:
            return {
                "status": "no_bar",
                "progress": 0.0,
                "volume": 0,
                "target_volume": self.volume_bar_size,
            }
        
        progress = self.current_bar_volume / self.volume_bar_size if self.volume_bar_size > 0 else 0.0
        
        return {
            "status": "accumulating",
            "symbol": self.current_symbol,
            "progress": progress,
            "volume": self.current_bar_volume,
            "target_volume": self.volume_bar_size,
            "tick_count": len(self.current_bar_ticks),
            "start_ts": self.current_bar_start_ts,
        }
    
    def calculate_infotime_factor(self) -> float:
        """
        計算 F_InfoTime 因子
        
        F_InfoTime = current_interval / long_term_avg_freq
        
        其中：
        - current_interval: 當前 Volume Bar 的間隔時間
        - long_term_avg_freq: 長期平均頻率（最近 N 個 Bar 的平均間隔時間）
        
        Returns:
            float: F_InfoTime 因子值
                - > 1.0: 當前信息流較慢（市場沉寂）
                - = 1.0: 正常信息流
                - < 1.0: 當前信息流較快（市場活躍）
        """
        if len(self.bar_intervals) < 2:
            return 1.0  # 數據不足，返回預設值
        
        # 當前間隔（最後兩個 Bar 的間隔）
        current_interval = self.bar_intervals[-1]
        
        # 長期平均間隔（最近 N 個 Bar 的平均）
        long_term_avg_interval = sum(self.bar_intervals) / len(self.bar_intervals)
        
        if long_term_avg_interval <= 0:
            return 1.0
        
        # F_InfoTime = current_interval / long_term_avg_interval
        infotime_factor = current_interval / long_term_avg_interval
        
        return infotime_factor
    
    def get_recent_bars(self, n: int = 10) -> List[VolumeBar]:
        """
        取得最近 N 個已完成的 VolumeBar
        
        Args:
            n: 要取得的 Bar 數量
        
        Returns:
            List[VolumeBar]: 最近的 VolumeBar 列表
        """
        return list(self.completed_bars)[-n:]
    
    def reset(self):
        """重置生成器狀態（用於新 episode 開始）"""
        self.current_bar_ticks = []
        self.current_bar_volume = 0
        self.current_bar_price_volume_sum = 0.0
        self.current_bar_start_ts = None
        self.current_symbol = None
        self.completed_bars.clear()
        self.bar_intervals.clear()


# ============================================================================
# 使用範例與測試輔助函數
# ============================================================================

def example_usage():
    """
    使用範例：展示如何使用 InfoTimeBarGenerator
    """
    from data_feed.tick_handler import MockSinopacAPI, SinopacConverter
    
    # 1. 建立 Mock API 和 Converter
    mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
    converter = SinopacConverter()
    
    # 2. 建立 Volume Bar 生成器
    generator = InfoTimeBarGenerator(volume_bar_size=1000)  # 測試用小值：1000
    
    # 3. 處理多個 Tick，產生 VolumeBar
    print("=== 處理 Tick 並產生 VolumeBar ===")
    bar_count = 0
    for i in range(100):  # 處理 100 個 Tick
        raw_tick = mock_api.get_next_raw_tick()
        unified_tick = converter.convert_to_unified(raw_tick)
        
        volume_bar = generator.add_tick(unified_tick)
        
        if volume_bar:
            bar_count += 1
            print(f"\nVolumeBar #{bar_count}:")
            print(f"  Symbol: {volume_bar.symbol}")
            print(f"  VWAP: {volume_bar.vwap:.2f}")
            print(f"  Volume: {volume_bar.total_volume}")
            print(f"  Tick Count: {volume_bar.tick_count}")
            print(f"  Price Range: {volume_bar.low_price:.2f} ~ {volume_bar.high_price:.2f}")
            print(f"  Time Range: {volume_bar.start_ts:.2f} ~ {volume_bar.end_ts:.2f}")
            
            # 計算 F_InfoTime
            infotime = generator.calculate_infotime_factor()
            print(f"  F_InfoTime: {infotime:.4f}")
    
    # 4. 顯示當前進度
    print(f"\n=== 當前 VolumeBar 進度 ===")
    progress = generator.get_current_bar_progress()
    print(f"進度: {progress['progress']*100:.1f}% ({progress['volume']}/{progress['target_volume']})")
    print(f"Tick 數量: {progress['tick_count']}")
    
    # 5. 取得最近的 VolumeBar
    print(f"\n=== 最近的 VolumeBar ===")
    recent_bars = generator.get_recent_bars(n=3)
    for i, bar in enumerate(recent_bars, 1):
        print(f"Bar {i}: VWAP={bar.vwap:.2f}, Volume={bar.total_volume}")


if __name__ == "__main__":
    # 執行使用範例
    example_usage()

