import easyocr
from typing import Tuple

# Load once (important)
reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_image(image_path: str) -> Tuple[str, float]:
    """
    Returns extracted text and average confidence.
    """

    try:
        results = reader.readtext(image_path)

        if not results:
            return "", 0.0

        texts = []
        confidences = []

        for bbox, text, conf in results:
            texts.append(text)
            confidences.append(conf)

        final_text = " ".join(texts)
        avg_conf = sum(confidences) / len(confidences)

        return final_text, avg_conf

    except Exception as e:
        print(f"OCR Error: {e}")
        return "", 0.0