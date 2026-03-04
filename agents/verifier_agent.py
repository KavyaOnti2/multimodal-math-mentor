import sympy as sp


def verify_symbolic_equivalence(ans1: str, ans2: str) -> bool:
    try:
        expr1 = sp.sympify(ans1)
        expr2 = sp.sympify(ans2)
        return sp.simplify(expr1 - expr2) == 0
    except Exception:
        return False


def verifier_agent(parsed_output, solver_output):

    result = {
        "verdict": "unknown",
        "confidence": 0.0,
        "reason": "",
    }

    # --------------------------------------------------
    #  Solver failure
    # --------------------------------------------------
    if not solver_output or solver_output.get("status") != "success":
        result["verdict"] = "fail"
        result["confidence"] = 0.0
        result["reason"] = "Solver did not return success."
        return result

    try:
        topic = parsed_output.get("topic", "")
        answer = solver_output.get("final_answer", "")

        # --------------------------------------------------
        # Algebra verification
        # --------------------------------------------------
        if topic == "algebra":

            problem_text = parsed_output.get("problem_text", "")
            cleaned_answer = answer.replace("Factored:", "").replace("Simplified:", "").strip()

            # Case 1 Equation solving
            if "=" in problem_text and "Solutions" in answer:
                return {
                    "verdict": "correct",
                    "confidence": 0.9,
                    "reason": "Equation solved successfully."
                }

            # Case 2 Factoring / Simplifying
            try:
                expr_original = sp.sympify(problem_text)
                expr_answer = sp.sympify(cleaned_answer)

                if sp.expand(expr_answer) == sp.expand(expr_original):
                    return {
                        "verdict": "correct",
                        "confidence": 0.9,
                        "reason": "Expression verified via symbolic expansion."
                    }

            except Exception:
                pass

            return {
                "verdict": "uncertain",
                "confidence": 0.5,
                "reason": "Algebra verification incomplete."
            }

        # --------------------------------------------------
        # 3️ Calculus verification
        # --------------------------------------------------
        if topic == "calculus":
            if "Derivative" in answer or "Limit" in answer:
                return {
                    "verdict": "correct",
                    "confidence": 0.9,
                    "reason": "Calculus result format valid."
                }

        # --------------------------------------------------
        # 4️ Probability verification
        # --------------------------------------------------
        if topic == "probability":
            if "/" in answer or "Probability" in answer:
                return {
                    "verdict": "correct",
                    "confidence": 0.8,
                    "reason": "Probability format valid."
                }

        # --------------------------------------------------
        # 5️ Linear algebra
        # --------------------------------------------------
        if topic == "linear_algebra":
            return {
                "verdict": "correct",
                "confidence": 0.85,
                "reason": "Linear algebra format valid."
            }

        # --------------------------------------------------
        # fallback
        # --------------------------------------------------
        return {
            "verdict": "uncertain",
            "confidence": 0.5,
            "reason": "Unable to fully verify."
        }

    except Exception as e:
        return {
            "verdict": "uncertain",
            "confidence": 0.4,
            "reason": f"Verification error: {str(e)}"
        }