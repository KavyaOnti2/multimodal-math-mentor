import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load embedding model (lightweight & fast)
model = SentenceTransformer("all-MiniLM-L6-v2")


# =====================================================
# LOAD KNOWLEDGE FILES
# =====================================================
def load_knowledge_base(folder_path="rag/knowledge_base"):
    documents = []

    for file in os.listdir(folder_path):
        if file.endswith(".txt"):
            file_path = os.path.join(folder_path, file)
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                documents.extend([line.strip() for line in lines if line.strip()])

    return documents


# =====================================================
# BUILD VECTOR INDEX
# =====================================================
def build_vector_store():
    docs = load_knowledge_base()

    if not docs:
        return None, []

    embeddings = model.encode(docs)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype("float32"))

    return index, docs