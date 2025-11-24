"""
股票元資料：提供股票代號到公司名稱的對應
"""
from typing import Optional, Dict
from jgod.data.db import get_connection


# 內建常用股票名稱對應表（優先使用資料庫，fallback 到這個）
_STOCK_NAMES: Dict[str, str] = {
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2308": "台達電",
    "1301": "台塑",
    "1303": "南亞",
    "2303": "聯電",
    "2882": "國泰金",
    "2881": "富邦金",
    "2891": "中信金",
    "2886": "兆豐金",
    "2892": "第一金",
    "2884": "玉山金",
    "2885": "元大金",
    "2880": "華南金",
    "2002": "中鋼",
    "2207": "和泰車",
    "2357": "華碩",
    "2382": "廣達",
    "2412": "中華電",
    "3008": "大立光",
    "3045": "台灣大",
    "3711": "日月光投控",
    "4938": "和碩",
    "5347": "世界先進",
    "5871": "中租-KY",
    "6415": "矽力-KY",
    "8046": "南電",
    "8454": "富邦媒",
    "9910": "豐泰",
    "1101": "台泥",
    "1102": "亞泥",
    "1216": "統一",
    "1402": "遠東新",
    "1476": "儒鴻",
    "1504": "東元",
    "1605": "華新",
    "1702": "南僑",
    "1802": "台玻",
    "1904": "正新",
    "2105": "正新",
    "2201": "裕隆",
    "2301": "光寶科",
    "2324": "仁寶",
    "2344": "華邦電",
    "2379": "瑞昱",
    "2383": "台光電",
    "2395": "研華",
    "2408": "南亞科",
    "2449": "京元電子",
    "2202": "中鋼",
}


def get_stock_display_name(symbol: str) -> str:
    """
    取得股票顯示名稱（代號 + 公司名稱）
    
    優先從資料庫查詢，如果沒有則使用內建對應表
    
    Args:
        symbol: 股票代號（例如：2330）
    
    Returns:
        顯示名稱（例如："2330 台積電"），如果找不到公司名稱則回傳 "2330"
    """
    # 先嘗試從資料庫查詢（如果未來有建立 tw_stock_meta 表）
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 檢查是否有 tw_stock_meta 表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tw_stock_meta'
        """)
        
        if cursor.fetchone():
            # 查詢股票名稱
            cursor.execute("""
                SELECT stock_name FROM tw_stock_meta 
                WHERE stock_id = ?
            """, (symbol,))
            
            result = cursor.fetchone()
            if result:
                stock_name = result[0]
                conn.close()
                return f"{symbol} {stock_name}"
        
        conn.close()
    except Exception:
        # 資料庫查詢失敗，繼續使用內建對應表
        pass
    
    # Fallback：使用內建對應表
    stock_name = _STOCK_NAMES.get(symbol)
    if stock_name:
        return f"{symbol} {stock_name}"
    
    # 如果都找不到，只回傳代號
    return symbol


def get_stock_name_only(symbol: str) -> Optional[str]:
    """
    只取得公司名稱（不含代號）
    
    Args:
        symbol: 股票代號
    
    Returns:
        公司名稱，如果找不到則回傳 None
    """
    display_name = get_stock_display_name(symbol)
    if " " in display_name:
        return display_name.split(" ", 1)[1]
    return None

