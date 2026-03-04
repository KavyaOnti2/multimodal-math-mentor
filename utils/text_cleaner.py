import re


def clean_math_text(text: str) -> str:
    """
    Cleans noisy OCR/ASR math text.
    Simple but high-impact normalization.
    """

    if not text:
        return ""

    t = text

    # ---------- common OCR fixes ----------
    replacements = {
        "/R": "R",
        " v ": " -> ",
        " iS": " is",
        "IS": "is",
        "ﬁ": "fi",
        "ﬂ": "fl",
    }

    for k, v in replacements.items():
        t = t.replace(k, v)

    # normalize spaces
    t = re.sub(r"\s+", " ", t)

    # remove weird chars but keep math symbols
    t = re.sub(r"[^a-zA-Z0-9=+\-*/^().,| <>]", " ", t)

    return t.strip()