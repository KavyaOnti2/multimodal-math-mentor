import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Confidence thresholds (used for HITL)
OCR_CONF_THRESHOLD = 0.6
ASR_CONF_THRESHOLD = 0.6
VERIFIER_CONF_THRESHOLD = 0.7

# RAG settings
TOP_K = 3