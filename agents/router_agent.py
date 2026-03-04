from typing import Dict


def router_agent(parsed_output: Dict) -> Dict:
    """
    Decide what the system should do next.
    """

    if not parsed_output:
        return {"route": "clarify", "reason": "No parsed output"}

    # 🔹 If parser says clarification needed
    if parsed_output.get("needs_clarification", False):
        return {
            "route": "clarify",
            "reason": "Parser detected ambiguity"
        }

    text = parsed_output.get("problem_text", "").lower()

    explain_keywords = [
        "explain",
        "why",
        "concept",
        "intuition",
        "meaning",
    ]

    if any(k in text for k in explain_keywords):
        return {
            "route": "explain",
            "reason": "User asking for explanation"
        }

    return {
        "route": "solve",
        "reason": "Clear math problem detected"
    }