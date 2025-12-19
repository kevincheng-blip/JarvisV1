"""
Universe loader for OR-OS (TOP50).
"""
from typing import List

# MVP: Fixed TOP50 list (Taiwan stocks)
# TODO: Replace with dynamic loader from DB/config
TOP50_SYMBOLS = [
    "2330", "2317", "2454", "2308", "2412", "2303", "2882", "2881", "2891", "2886",
    "1301", "2892", "2884", "2880", "1303", "2885", "2002", "2207", "2357", "2382",
    "2883", "2379", "2324", "2301", "2887", "2890", "2408", "3008", "2888", "3045",
    "2371", "2383", "2409", "2889", "2353", "3034", "2305", "2327", "2345", "2309",
    "2311", "2328", "2344", "2302", "2313", "2329", "2354", "2306", "2312", "2347",
]


def get_top50_universe() -> List[str]:
    """Get TOP50 universe symbols."""
    return TOP50_SYMBOLS.copy()


def load_universe(universe_name: str) -> List[str]:
    """
    Load universe by name.
    
    Args:
        universe_name: "top50" or other universe names
        
    Returns:
        List of symbol strings
    """
    if universe_name.lower() == "top50":
        return get_top50_universe()
    else:
        raise ValueError(f"Unknown universe: {universe_name}")
