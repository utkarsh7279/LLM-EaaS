from app.utils.metrics import detect_regression


def test_detect_regression_flags_drop() -> None:
    result = detect_regression(baseline_mean=4.0, candidate_mean=3.6, threshold=0.05)
    assert result.regression_detected is True


def test_detect_regression_no_drop() -> None:
    result = detect_regression(baseline_mean=4.0, candidate_mean=3.9, threshold=0.05)
    assert result.regression_detected is False
