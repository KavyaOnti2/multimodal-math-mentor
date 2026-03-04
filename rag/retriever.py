from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os

# ================= LOAD MODEL =================
model = SentenceTransformer("all-MiniLM-L6-v2")

INDEX_PATH = "rag/faiss_index.bin"
TEXT_PATH = "data/math_knowledge.txt"


# ================= BUILD INDEX =================
def build_index():
    if not os.path.exists(TEXT_PATH):
        return None, None

    with open(TEXT_PATH, "r", encoding="utf-8") as f:
        docs = [line.strip() for line in f if line.strip()]

    embeddings = model.encode(docs)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))

    faiss.write_index(index, INDEX_PATH)

    return index, docs


# ================= LOAD INDEX =================
def load_index():
    if not os.path.exists(INDEX_PATH):
        return build_index()

    index = faiss.read_index(INDEX_PATH)

    if not os.path.exists(TEXT_PATH):
        return None, None

    with open(TEXT_PATH, "r", encoding="utf-8") as f:
        docs = [line.strip() for line in f if line.strip()]

    return index, docs


# ================= RETRIEVE =================
def retrieve_context(query: str, k: int = 2):
    index, docs = load_index()

    if index is None or docs is None:
        return []

    # encode query
    q_emb = model.encode([query])
    q_emb = np.array(q_emb).astype("float32")

    # FAISS search
    D, I = index.search(q_emb, k)

    results = []

    for idx, dist in zip(I[0], D[0]):
        if idx < len(docs):
            #  convert L2 distance → similarity score
            score = 1 / (1 + dist)
            results.append((docs[idx], float(score)))

    return results