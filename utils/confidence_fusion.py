# utils/confidence_fusion.py

def compute_final_confidence(
    input_conf: float,
    parsed_output: dict | None,
    solver_output: dict | None,
) -> float:
    """
    Production-style confidence fusion.
    """

    score = input_conf

    # 🔹 parser penalty
    if parsed_output:
        if parsed_output.get("needs_clarification"):
            score *= 0.7
        if parsed_output.get("topic") == "unknown":
            score *= 0.6

    # 🔹 solver penalty
    if solver_output:
        status = solver_output.get("status")

        if status == "error":
            score *= 0.4
        elif status == "unsupported":
            score *= 0.5
        elif status == "success":
            score = min(1.0, score + 0.1)

    return round(max(0.0, min(score, 1.0)), 3)