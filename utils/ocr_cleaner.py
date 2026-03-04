import re

def clean_ocr_math(text: str) -> str:
    if not text:
        return text

    t = text

    # =============================
    # ✅ Your existing strong fixes
    # =============================
    # OCR command corrections
    t = t.replace("So1ve", "Solve")
    t = t.replace("S0lve", "Solve")
    t = t.replace("SoIve", "Solve")
    t = t.replace("So|ve", "Solve")
    t = t.replace("x2", "x^2")
    t = t.replace("X2", "x^2")
    t = t.replace("Sx", "5x")
    t = t.replace("sx", "5x")


    # fix spaced powers: x 2 → x^2
    t = re.sub(r"\bx\s+(\d)", r"x^\1", t)
     # remove double spaces
    t = re.sub(r"\s+", " ", t)

    return t.strip()

    # =============================
    # 🔥 NEW: function OCR fixes
    # =============================
    replacements = {
        "/R": "R",
        " v ": " -> ",
        " iS": " is",
        " f (x)": " f(x)",
        "|x - l|": "|x-1|",
        "|x - I|": "|x-1|",
        "l": "1",  # careful but useful for OCR math
    }

    for k, v in replacements.items():
        t = t.replace(k, v)

    # =============================
    # 🔥 NEW: fraction cleanup
    # =============================
    t = re.sub(r"\(\s*", "(", t)
    t = re.sub(r"\s*\)", ")", t)

    # =============================
    # 🔥 normalize spaces
    # =============================
    t = re.sub(r"\s+", " ", t)

    return t.strip()