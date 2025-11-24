import datetime
import random

def is_market_open(date=None):
    """
    簡化版：只判斷是不是週一～週五。
    之後要接 FinMind 假日 API 再升級。
    """
    if date is None:
        date = datetime.datetime.today().strftime("%Y-%m-%d")

    weekday = datetime.datetime.today().weekday()  # Monday=0, Sunday=6
    # 0~4 = 一到五 開市；5,6 = 六日 休市
    if weekday >= 5:
        return False
    return True


def get_taiwan_market_data():
    """
    暫時版：不連 FinMind，用假資料讓戰情室可以正常運作。
    之後接上 FinMind 時，只要改這個函式內容即可。
    """
    today = datetime.datetime.today().strftime("%Y-%m-%d")

    if not is_market_open(today):
        return {
            "market_open": False,
            "message": "今日為週末或假日（暫用測試版判定），未提供即時數據。",
        }

    # ===== 下面全部是「假數字」，先讓系統能動 =====
    # 你可以改成你想要的預設值
    taiex_close = 17850 + random.randint(-50, 50)
    taiex_change = random.randint(-120, 120)
    taiex_volume = 2800_000_000 + random.randint(-300_000_000, 300_000_000)

    tsmc_close = 700 + random.randint(-10, 10)
    tsmc_change = random.randint(-8, 8)

    foreign = random.randint(-50, 80) * 10**8   # 假設單位：億元
    trust = random.randint(-10, 20) * 10**8
    dealer = random.randint(-15, 15) * 10**8

    return {
        "market_open": True,
        "taiex_close": taiex_close,
        "taiex_change": taiex_change,
        "taiex_volume": taiex_volume,
        "tsmc_close": tsmc_close,
        "tsmc_change": tsmc_change,
        "foreign": foreign,
        "trust": trust,
        "dealer": dealer,
        "message": "目前為測試用假資料，之後會接上 FinMind 真實數據。",
    }
