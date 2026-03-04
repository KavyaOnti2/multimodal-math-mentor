# utils/memory_learning.py

def get_failure_patterns(system_memory: list) -> dict:
    """
    Learn weak areas from history.
    """
    stats = {
        "algebra_fail": 0,
        "calculus_fail": 0,
        "ocr_noise": 0,
    }

    for entry in system_memory:
        parsed = entry.get("parsed_output", {})
        status = entry.get("verifier_outcome")

        topic = parsed.get("topic")

        if status in ["error", "unsupported"]:
            if topic == "algebra":
                stats["algebra_fail"] += 1
            if topic == "calculus":
                stats["calculus_fail"] += 1

        text = entry.get("original_input", "")
        if "^" not in text and "x2" in text:
            stats["ocr_noise"] += 1

    return stats