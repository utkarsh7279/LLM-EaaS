"""Advanced metrics and statistical analysis."""

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats


@dataclass
class AdvancedMetrics:
    """Advanced statistical metrics for evaluation results."""

    mean_score: float
    median_score: float
    std_dev: float
    min_score: float
    max_score: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_95: float
    percentile_99: float
    confidence_interval_95: tuple[float, float]
    confidence_interval_99: tuple[float, float]
    skewness: float
    kurtosis: float
    coefficient_of_variation: float
    safety_fail_rate: float
    variance: float


def calculate_advanced_metrics(
    scores: list[float], safety_failures: int | None = None, total_items: int | None = None
) -> AdvancedMetrics:
    """Calculate comprehensive statistical metrics for evaluation results.

    Args:
        scores: List of numerical scores from evaluations
        safety_failures: Number of safety failures (optional)
        total_items: Total number of items evaluated (optional)

    Returns:
        AdvancedMetrics dataclass with all statistical measures
    """
    if not scores:
        raise ValueError("Cannot calculate metrics for empty score list")

    scores_array = np.array(scores)
    n = len(scores_array)

    # Basic statistics
    mean = float(np.mean(scores_array))
    median = float(np.median(scores_array))
    std_dev = float(np.std(scores_array, ddof=1) if n > 1 else 0)
    variance = float(np.var(scores_array, ddof=1) if n > 1 else 0)
    min_score = float(np.min(scores_array))
    max_score = float(np.max(scores_array))

    # Percentiles
    p25 = float(np.percentile(scores_array, 25))
    p50 = float(np.percentile(scores_array, 50))
    p75 = float(np.percentile(scores_array, 75))
    p95 = float(np.percentile(scores_array, 95))
    p99 = float(np.percentile(scores_array, 99))

    # Confidence intervals (95% and 99%)
    sem = stats.sem(scores_array)  # Standard error of the mean
    ci_95 = stats.t.interval(0.95, n - 1, loc=mean, scale=sem)
    ci_99 = stats.t.interval(0.99, n - 1, loc=mean, scale=sem)

    # Distribution shape
    skewness_val = float(stats.skew(scores_array)) if n > 2 else 0.0
    kurtosis_val = float(stats.kurtosis(scores_array)) if n > 3 else 0.0

    # Coefficient of variation (ratio of std dev to mean)
    cv = (std_dev / mean) if mean != 0 else 0.0
    cv = float(cv)

    # Safety fail rate
    if safety_failures is not None and total_items is not None:
        fail_rate = safety_failures / total_items if total_items > 0 else 0.0
    else:
        fail_rate = 0.0

    return AdvancedMetrics(
        mean_score=mean,
        median_score=median,
        std_dev=std_dev,
        min_score=min_score,
        max_score=max_score,
        percentile_25=p25,
        percentile_50=p50,
        percentile_75=p75,
        percentile_95=p95,
        percentile_99=p99,
        confidence_interval_95=(float(ci_95[0]), float(ci_95[1])),
        confidence_interval_99=(float(ci_99[0]), float(ci_99[1])),
        skewness=skewness_val,
        kurtosis=kurtosis_val,
        coefficient_of_variation=cv,
        safety_fail_rate=fail_rate,
        variance=variance,
    )


def compare_distributions(scores_1: list[float], scores_2: list[float]) -> dict[str, Any]:
    """Perform statistical comparison between two distributions.

    Returns:
        Dictionary with t-test, Mann-Whitney U test, and effect size
    """
    if not scores_1 or not scores_2:
        raise ValueError("Both score lists must be non-empty")

    arr1 = np.array(scores_1)
    arr2 = np.array(scores_2)

    # Parametric test (t-test)
    t_stat, t_pval = stats.ttest_ind(arr1, arr2)

    # Non-parametric test (Mann-Whitney U)
    u_stat, u_pval = stats.mannwhitneyu(arr1, arr2, alternative="two-sided")

    # Effect size (Cohen's d)
    cohens_d = (np.mean(arr1) - np.mean(arr2)) / np.sqrt((np.var(arr1) + np.var(arr2)) / 2)

    # Welch's t-test (for unequal variances)
    welch_t, welch_p = stats.ttest_ind(arr1, arr2, equal_var=False)

    return {
        "t_test": {"statistic": float(t_stat), "p_value": float(t_pval), "significant": float(t_pval) < 0.05},
        "mann_whitney_u": {"statistic": float(u_stat), "p_value": float(u_pval), "significant": float(u_pval) < 0.05},
        "welch_t_test": {"statistic": float(welch_t), "p_value": float(welch_p), "significant": float(welch_p) < 0.05},
        "cohens_d": float(cohens_d),
        "effect_size_interpretation": interpret_cohens_d(cohens_d),
        "mean_difference": float(np.mean(arr1) - np.mean(arr2)),
    }


def interpret_cohens_d(cohens_d: float) -> str:
    """Interpret Cohen's d effect size."""
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"
