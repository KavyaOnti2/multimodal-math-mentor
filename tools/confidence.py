def is_low_confidence(score: float, threshold: float) -> bool:
    return score < threshold