# ============================================================
# PART 1 — IMPORTS
# ============================================================

from sentence_transformers import SentenceTransformer

from app import config

# ============================================================
# PART 2 — LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer(config.EMBEDDING_MODEL)  # 384

print("Embedding model ready!")


# ============================================================
# PART 3 — EMBED MANY TEXTS (for code chunks)
# ============================================================


def embed_texts(texts):

    embeddings = model.encode(texts, batch_size=32)

    return embeddings.tolist()


# ============================================================
# PART 4 — EMBED ONE TEXT (for the user question)
# ============================================================


def embed_text(text):

    return model.encode(text).tolist()


# ============================================================
# PART 5 — TEST
# ============================================================

if __name__ == "__main__":

    vector = embed_text("where is the login api")

    print(f"Embedding size: {len(vector)}")
    print(f"First 5 numbers: {vector[:5]}")
