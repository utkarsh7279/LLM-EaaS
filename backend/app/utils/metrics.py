"""Metrics helpers for experiment comparison."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegressionResult:
    """Outcome of regression detection."""

    regression_detected: bool
    delta_mean_score: float
    drop_ratio: float


def detect_regression(baseline_mean: float, candidate_mean: float, threshold: float = 0.05) -> RegressionResult:
    """Detect score regression relative to the baseline mean score."""
    if baseline_mean <= 0:
        raise ValueError("Baseline mean score must be positive")

    delta = candidate_mean - baseline_mean
    drop_ratio = max(0.0, (baseline_mean - candidate_mean) / baseline_mean)
    regression = drop_ratio > threshold

    return RegressionResult(
        regression_detected=regression,
        delta_mean_score=delta,
        drop_ratio=drop_ratio,
    )
