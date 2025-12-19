"""
Resonance tag and conflict score calculation (MVP rules).
"""
from typing import Dict, Literal

from jgod.oracle.schemas import ForecastHorizon


def calculate_conflict_score(forecast_matrix: Dict[str, ForecastHorizon]) -> float:
    """
    Calculate conflict score (0-1): proportion of horizons with opposite directions.
    
    Args:
        forecast_matrix: Dict of horizon -> ForecastHorizon
        
    Returns:
        Conflict score (0.0 = no conflict, 1.0 = all conflict)
    """
    if not forecast_matrix:
        return 0.0
    
    directions = []
    for horizon in ["T1", "T5", "T10", "T20", "TM"]:
        if horizon in forecast_matrix:
            directions.append(forecast_matrix[horizon].direction)
    
    if len(directions) < 2:
        return 0.0
    
    # Count opposite directions
    up_count = sum(1 for d in directions if d == "UP")
    down_count = sum(1 for d in directions if d == "DOWN")
    side_count = sum(1 for d in directions if d == "SIDE")
    
    total = len(directions)
    if total == 0:
        return 0.0
    
    # Conflict = proportion of directions that are minority
    if up_count > down_count:
        conflict = (down_count + side_count) / total
    elif down_count > up_count:
        conflict = (up_count + side_count) / total
    else:
        # Equal or all SIDE
        conflict = 0.5
    
    return round(conflict, 3)


def calculate_resonance_tag(forecast_matrix: Dict[str, ForecastHorizon]) -> Literal["STRONG", "MIXED", "SHORT_SPIKE", "LONG_WAVE"]:
    """
    Calculate resonance tag based on forecast matrix consistency.
    
    Rules (MVP):
    - STRONG: T1 & T5 same direction, and T20 not opposite
    - SHORT_SPIKE: T1 strong same direction, but T5/T20 opposite at least one
    - LONG_WAVE: T20/TM same direction but T1 noise (optional)
    - MIXED: Other cases
    """
    if not forecast_matrix:
        return "MIXED"
    
    t1_dir = forecast_matrix.get("T1")
    t5_dir = forecast_matrix.get("T5")
    t20_dir = forecast_matrix.get("T20")
    tm_dir = forecast_matrix.get("TM")
    
    # STRONG: T1 & T5 same direction, and T20 not opposite
    if t1_dir and t5_dir:
        t1_d = t1_dir.direction
        t5_d = t5_dir.direction
        if t1_d == t5_d and t1_d != "SIDE":
            if t20_dir:
                t20_d = t20_dir.direction
                if t20_d == "SIDE" or t20_d == t1_d:
                    return "STRONG"
            else:
                return "STRONG"
    
    # SHORT_SPIKE: T1 strong same direction, but T5/T20 opposite at least one
    if t1_dir and t1_dir.direction != "SIDE":
        t1_d = t1_dir.direction
        if t5_dir and t5_dir.direction != t1_d and t5_dir.direction != "SIDE":
            return "SHORT_SPIKE"
        if t20_dir and t20_dir.direction != t1_d and t20_dir.direction != "SIDE":
            return "SHORT_SPIKE"
    
    # LONG_WAVE: T20/TM same direction but T1 noise
    if (t20_dir and tm_dir and 
        t20_dir.direction == tm_dir.direction and 
        t20_dir.direction != "SIDE"):
        if t1_dir and (t1_dir.direction == "SIDE" or t1_dir.direction != t20_dir.direction):
            return "LONG_WAVE"
    
    return "MIXED"
