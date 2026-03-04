import re
from typing import Dict
import sympy as sp

import re

def _clean_equation(text: str) -> str:
    """
    Convert natural language math to symbolic math.
    Handles ASR noise + implicit multiplication.
    """

    if not text:
        return text

    t = text.lower()

    # ----------------------------------
    # Natural language replacements
    # ----------------------------------
    replacements = {
        "square": "^2",
        "cube": "^3",
        "plus": "+",
        "minus": "-",
        "equal to": "=",
        "equals": "=",
        "equal": "=",
        "into": "*",
        "times": "*",
        "multiply": "*",
    }

    for word, symbol in replacements.items():
        t = t.replace(word, symbol)

    # ----------------------------------
    # Remove command words safely
    # ----------------------------------
    t = re.sub(r"\b(solve|find|evaluate|compute|factor|expand|simplify)\b", "", t)

    # ----------------------------------
    # Power conversion
    # ----------------------------------
    t = t.replace("^", "**")

    # Fix x2 → x**2
    t = re.sub(r"x2\b", "x**2", t)

    # ----------------------------------
    # Fix implicit multiplication
    # ----------------------------------

    # 3x → 3*x
    t = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", t)

    # x(x+1) → x*(x+1)
    # x(x+1) → x*(x+1)
    # but DO NOT break sin(x), cos(x), etc.
    t = re.sub(
        r"\b(?!sin|cos|tan|log|ln|exp)([a-zA-Z])\(",
        r"\1*(",
        t
    )

    # (x+1)(x+2) → (x+1)*(x+2)
    t = re.sub(r"\)\s*\(", ")*(", t)

    # sin x → sin(x)
    t = re.sub(r"(sin|cos|tan|log|ln)\s+([a-zA-Z])", r"\1(\2)", t)

    # ----------------------------------
    # Normalize equals
    # ----------------------------------
    t = t.replace(" = ", "=")

    # If OCR added multiple '=' keep first equation only
    if t.count("=") > 1:
        parts = t.split("=")
        t = parts[0] + "=" + parts[1]

    # Clean spaces
    t = re.sub(r"\s+", " ", t).strip()

    return t

# =====================================================
# ALGEBRA SOLVER
# =====================================================

def _solve_algebra(text: str, variables):

    var_symbol = sp.symbols(variables[0] if variables else "x")
    clean_text = _clean_equation(text)
    lower_text = text.lower()

    # =====================================================
    # HANDLE SIMPLIFY / FACTOR / EXPAND FIRST
    # =====================================================
    if "simplify" in lower_text or "/" in clean_text:
        try:
            # extract expression after simplify
            match = re.search(r"simplify\s*(.*)", text, re.I)
            expr_str = match.group(1) if match else clean_text

            expr = sp.sympify(expr_str)
            simplified = sp.simplify(expr)

            return f"Simplified: {simplified}"

        except Exception:
            raise ValueError("Could not simplify expression")

    if "factor" in lower_text:
        expr_str = clean_text.replace("factor", "")
        expr = sp.sympify(expr_str)
        return f"Factored: {sp.factor(expr)}"

    if "expand" in lower_text:
        expr_str = clean_text.replace("expand", "")
        expr = sp.sympify(expr_str)
        return f"Expanded: {sp.expand(expr)}"

    # =====================================================
    # HANDLE EQUATIONS (YOUR ORIGINAL LOGIC)
    # =====================================================
    if "=" not in clean_text:
        raise ValueError("No equation found")

    lhs, rhs = clean_text.split("=")

    lhs_expr = sp.sympify(lhs)
    rhs_expr = sp.sympify(rhs)

    equation = sp.Eq(lhs_expr, rhs_expr)
    solutions = sp.solve(equation, var_symbol)

    return f"Solutions: {solutions}"

# =====================================================
# CALCULUS SOLVER
# =====================================================

def _solve_calculus(text: str, variables):
    import sympy as sp
    import re

    x = sp.symbols(variables[0] if variables else "x")
    t = text.lower()

    # -------------------------------------------------
    # DERIVATIVE
    # -------------------------------------------------
    if "derivative" in t or "differentiate" in t:

        # remove command words
        expr_text = re.sub(
            r"(derivative of|differentiate|find)",
            "",
            text,
            flags=re.I
        )

        expr_text = _clean_equation(expr_text)

        try:
            expr = sp.sympify(expr_text)
            result = sp.diff(expr, x)
            return f"Derivative: {result}"
        except Exception:
            raise ValueError("Could not compute derivative")

    # -------------------------------------------------
    # LIMIT
    # -------------------------------------------------
    if "limit" in t:

        try:
            # extract expression
            expr_text = re.sub(r"limit\s*of", "", text, flags=re.I)
            expr_text = re.sub(r"as.*", "", expr_text, flags=re.I)
            expr_text = _clean_equation(expr_text.strip())

            expr = sp.sympify(expr_text)

            # detect approaching value
            if "0" in t:
                result = sp.limit(expr, x, 0)
            elif "infinity" in t or "∞" in t:
                result = sp.limit(expr, x, sp.oo)
            else:
                raise ValueError

            return f"Limit: {result}"

        except Exception:
            raise ValueError("Unsupported limit format")

    raise ValueError("Unsupported calculus problem")


# =====================================================
# PROBABILITY SOLVER (Upgraded for JEE Basic Level)
# =====================================================
def _solve_probability(text: str):
    t = text.lower()

    # ------------------------------
    # COIN PROBLEMS
    # ------------------------------
    if "coin" in t:

        # two coins
        if "two" in t:
            total_outcomes = 4  # HH, HT, TH, TT

            if "at least one head" in t:
                favorable = 3  # HH, HT, TH
                return f"Probability: {favorable}/{total_outcomes}"

            if "both heads" in t:
                return "Probability: 1/4"

            if "exactly one head" in t:
                return "Probability: 2/4"

            return "Probability: 1/4 or 1/2 depending on event"

        # single coin
        else:
            if "head" in t:
                return "Probability: 1/2"
            if "tail" in t:
                return "Probability: 1/2"

            return "Probability: 1/2"

    # ------------------------------
    # SINGLE DIE
    # ------------------------------
    if "die" in t or "dice" in t:

        # two dice
        if "two" in t:

            total_outcomes = 36

            # sum conditions
            if "sum is" in t:
                import re
                nums = re.findall(r"\d+", t)
                if nums:
                    target = int(nums[-1])

                    favorable = 0
                    for i in range(1, 7):
                        for j in range(1, 7):
                            if i + j == target:
                                favorable += 1

                    return f"Probability: {favorable}/{total_outcomes}"

            # at least one six
            if "at least one 6" in t or "at least one six" in t:
                favorable = 11  # complement rule
                return f"Probability: {favorable}/{total_outcomes}"

            return "Probability depends on event (36 total outcomes)"

        # single die
        else:
            total_outcomes = 6

            if "even" in t:
                return "Probability: 3/6"

            if "odd" in t:
                return "Probability: 3/6"

            if "prime" in t:
                return "Probability: 3/6"

            return "Probability: 1/6"

    raise ValueError("Unsupported probability problem")


# =====================================================
# LINEAR ALGEBRA SOLVER
# =====================================================
def _solve_linear_algebra(text: str):
    t = text.lower()

    # very basic determinant of 2x2
    nums = re.findall(r"-?\d+", t)
    if "det" in t:
        nums = list(map(int, re.findall(r"-?\d+", text)))
        if len(nums) >= 4:
            matrix = sp.Matrix([[nums[0], nums[1]],
                            [nums[2], nums[3]]])
            return f"Determinant: {matrix.det()}"


# =====================================================
# MAIN SOLVER AGENT
# =====================================================
def solver_agent(parsed_output: Dict) -> Dict:
    """
    Multi-domain math solver.
    """

    if not parsed_output:
        return {
            "status": "error",
            "final_answer": "",
            "reason": "No parsed output",
        }

    text = parsed_output.get("problem_text", "")
    topic = parsed_output.get("topic", "")
    variables = parsed_output.get("variables", ["x"])

    try:
        #  ALGEBRA
        if topic == "algebra":
            answer = _solve_algebra(text, variables)

        #  CALCULUS
        elif topic == "calculus":
            answer = _solve_calculus(text, variables)

        # PROBABILITY
        elif topic == "probability":
            answer = _solve_probability(text)

        # LINEAR ALGEBRA
        elif topic == "linear_algebra":
            answer = _solve_linear_algebra(text)

        else:
            return {
                "status": "unsupported",
                "final_answer": "",
                "reason": "Problem type not supported yet",
            }

        #  build generic reasoning steps
        steps = []

        if topic == "algebra":
            steps = [
                "1️⃣ Identified algebraic equation.",
                "2️⃣ Converted to symbolic form.",
                "3️⃣ Solved using SymPy.",
            ]

        elif topic == "calculus":
            steps = [
                "1️⃣ Identified calculus operation.",
                "2️⃣ Applied differentiation/limit rules.",
                "3️⃣ Simplified the result.",
            ]

        elif topic == "probability":
            steps = [
                "1️⃣ Identified probability scenario.",
                "2️⃣ Assumed fair experiment.",
                "3️⃣ Computed probability using formula.",
            ]

        elif topic == "linear_algebra":
            steps = [
                "1️⃣ Identified linear algebra problem.",
                "2️⃣ Applied matrix/vector rules.",
                "3️⃣ Computed final result.",
            ]

        return {
            "status": "success",
            "final_answer": answer,
            "steps": steps, 
            "reason": "Solved using domain solver",
    }

    except Exception as e:
        return {
            "status": "error",
            "final_answer": "",
            "reason": str(e),
        }