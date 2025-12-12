"""
Prediction Stability Metrics

Computes stability metrics from prediction timeline data to assess
prediction quality and drift over time.
"""

from typing import List, Dict, Literal, TypedDict


class TimelineItem(TypedDict):
    """Timeline item structure"""
    date: str
    final_score: float


class StabilityMetrics(TypedDict):
    """Stability metrics output"""
    n_points: int
    score_std: float
    max_abs_delta: float
    trend_slope: float
    stability_grade: Literal["NO_DATA", "STABLE", "WATCH", "VOLATILE"]
    thresholds: Dict[str, float]


def compute_stability_metrics(
    items: List[TimelineItem],
    std_threshold_stable: float = 0.15,
    delta_threshold_stable: float = 0.30,
    std_threshold_watch: float = 0.30,
    delta_threshold_watch: float = 0.60,
    min_points: int = 5,
) -> StabilityMetrics:
    """
    Compute stability metrics from prediction timeline items.
    
    Args:
        items: List of timeline items with date and final_score
        std_threshold_stable: Standard deviation threshold for STABLE grade
        delta_threshold_stable: Max absolute delta threshold for STABLE grade
        std_threshold_watch: Standard deviation threshold for WATCH grade
        delta_threshold_watch: Max absolute delta threshold for WATCH grade
        min_points: Minimum number of points required (else NO_DATA)
    
    Returns:
        StabilityMetrics with computed values and grade
    """
    n_points = len(items)
    
    # If insufficient data, return NO_DATA
    if n_points < min_points:
        return StabilityMetrics(
            n_points=n_points,
            score_std=0.0,
            max_abs_delta=0.0,
            trend_slope=0.0,
            stability_grade="NO_DATA",
            thresholds={
                "std_threshold_stable": std_threshold_stable,
                "delta_threshold_stable": delta_threshold_stable,
                "std_threshold_watch": std_threshold_watch,
                "delta_threshold_watch": delta_threshold_watch,
                "min_points": min_points,
            },
        )
    
    # Extract scores (in chronological order - items are already sorted desc, so reverse)
    scores = [item["final_score"] for item in reversed(items)]
    
    # Compute standard deviation
    mean_score = sum(scores) / n_points
    variance = sum((s - mean_score) ** 2 for s in scores) / n_points
    score_std = variance ** 0.5
    
    # Compute max absolute day-to-day change
    max_abs_delta = 0.0
    for i in range(1, n_points):
        delta = abs(scores[i] - scores[i - 1])
        if delta > max_abs_delta:
            max_abs_delta = delta
    
    # Compute trend slope using simple linear regression (lightweight, no numpy)
    # y = mx + b, where x is index (0, 1, 2, ...) and y is score
    # slope m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    n = n_points
    sum_x = sum(range(n))
    sum_y = sum(scores)
    sum_xy = sum(i * scores[i] for i in range(n))
    sum_x_squared = sum(i * i for i in range(n))
    
    denominator = n * sum_x_squared - sum_x * sum_x
    if denominator != 0:
        trend_slope = (n * sum_xy - sum_x * sum_y) / denominator
    else:
        trend_slope = 0.0
    
    # Determine stability grade
    if score_std <= std_threshold_stable and max_abs_delta <= delta_threshold_stable:
        stability_grade: Literal["NO_DATA", "STABLE", "WATCH", "VOLATILE"] = "STABLE"
    elif score_std <= std_threshold_watch and max_abs_delta <= delta_threshold_watch:
        stability_grade = "WATCH"
    else:
        stability_grade = "VOLATILE"
    
    return StabilityMetrics(
        n_points=n_points,
        score_std=round(score_std, 4),
        max_abs_delta=round(max_abs_delta, 4),
        trend_slope=round(trend_slope, 4),
        stability_grade=stability_grade,
        thresholds={
            "std_threshold_stable": std_threshold_stable,
            "delta_threshold_stable": delta_threshold_stable,
            "std_threshold_watch": std_threshold_watch,
            "delta_threshold_watch": delta_threshold_watch,
            "min_points": min_points,
        },
    )

