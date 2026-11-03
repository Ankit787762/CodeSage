# ============================================================
# PART 1 — IMPORTS
# ============================================================

import os
from dotenv import load_dotenv


# ============================================================
# PART 2 — LOAD ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


# ============================================================
# PART 3 — MODEL SETTINGS
# ============================================================

GROQ_MODEL = "openai/gpt-oss-120b"
TEMPERATURE = 0.2

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_SIZE = 384


# ============================================================
# PART 4 — QDRANT SETTINGS
# ============================================================

COLLECTION_NAME = "code_chunks"


# ============================================================
# PART 5 — CHUNKING AND RETRIEVAL SETTINGS
# ============================================================

CHUNK_SIZE_LINES = 40
CHUNK_OVERLAP_LINES = 10
TOP_K = 5


# ============================================================
# PART 6 — STORAGE SETTINGS
# ============================================================

REPOS_DIR = "storage/repos"
MAX_ZIP_MB = 50

os.makedirs(REPOS_DIR, exist_ok=True)