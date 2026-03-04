from utils.text_cleaner import clean_math_text
import re
from typing import Dict


# =====================================================
# TOPIC CLASSIFIER
# =====================================================
def classify_topic(text: str) -> str:
    t = text.lower()

    # =====================================================
    #  AUTO-DETECT ALGEBRA FIRST 
    # =====================================================

    # detect equation automatically
    # auto-detect equation
    if "=" in text:
        return "algebra"

    # detect polynomial only if no calculus keyword
    if any(sym in text for sym in ["^", "x2", "x^"]) and not any(
        k in t for k in ["derivative", "differentiate", "limit", "integrate"]
    ):
        return "algebra"

    #  calculus
    if any(k in t for k in [
        "derivative",
        "differentiate",
        "limit",
        "integration",
        "integrate"
    ]):
        return "calculus"

    #  probability
    if any(k in t for k in [
        "probability",
        "dice",
        "coin",
        "chance"
    ]):
        return "probability"

    #  linear algebra
    if any(k in t for k in [
        "matrix",
        "vector",
        "determinant"
    ]):
        return "linear_algebra"

    #  algebra
    if any(k in t for k in [
        "solve",
        "equation",
        "quadratic",
        "roots",
        "function",
        "one-one",
        "onto",
        "injective",
        "surjective",
        "f(x)",
        "simplify",          
        "factor",            
        "expand",            
        "/",                 
        "^",
    ]):
        return "algebra"

    #  SAFE DEFAULT
    return "unknown"


# =====================================================
# VARIABLE EXTRACTOR
# =====================================================
def extract_variables(text: str):
    vars_found = re.findall(r"\b[a-zA-Z]\b", text)
    return sorted(list(set(vars_found)))


# =====================================================
# AMBIGUITY CHECK
# =====================================================
def check_ambiguity(text: str, topic: str) -> (bool, str):
    t = text.lower().strip()

    #  probability usually complete
    if topic == "probability":
        return False, ""

    #  too short
    if len(t) < 8:
        return True, "The question seems incomplete. Please provide more details."

    #  clearly incomplete commands
    incomplete_patterns = [
        r"^derivative of\s*$",
        r"^differentiate\s*$",
        r"^integrate\s*$",
        r"^limit of\s*$",
        r"^solve\s*$",
        r"^find\s*$",
    ]

    for pattern in incomplete_patterns:
        if re.match(pattern, t):
            return True, "The problem is incomplete. Please specify the full expression."

    #  calculus but missing expression
    if "derivative" in t or "differentiate" in t:
        remaining = (
            t.replace("derivative", "")
             .replace("differentiate", "")
             .strip()
        )
        if len(remaining) == 0:
            return True, "Please specify the function to differentiate."

    #  algebra equation expected but missing '='
    if any(k in t for k in ["solve", "equation", "roots"]):
        if "=" not in t and topic == "algebra":
            return True, "Equation seems incomplete. Please provide full equation."

    #  otherwise OK
    return False, ""


# =====================================================
# MAIN PARSER
# =====================================================
def parser_agent(raw_text: str) -> Dict:
    cleaned_text = clean_math_text(raw_text)

    topic = classify_topic(cleaned_text)
    variables = extract_variables(cleaned_text)

    needs_clarification, clarification_question = check_ambiguity(
        cleaned_text,
        topic
    )

    structured = {
        "problem_text": cleaned_text,
        "topic": topic,
        "variables": variables,
        "constraints": [],
        "needs_clarification": needs_clarification,
        "clarification_question": clarification_question,
    }

    return structured