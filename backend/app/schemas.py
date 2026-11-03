# ============================================================
# PART 1 — IMPORTS
# ============================================================

from pydantic import BaseModel, Field

# ============================================================
# PART 2 — UPLOAD RESPONSE
# ============================================================


class UploadResponse(BaseModel):
    repo_id: str
    files_indexed: int
    chunks_indexed: int


# ============================================================
# PART 3 — CHAT REQUEST
# ============================================================


class ChatRequest(BaseModel):
    repo_id: str
    question: str = Field(min_length=3, max_length=1000)


# ============================================================
# PART 4 — IMPACT ANALYSIS REQUEST
# ============================================================


class ImpactRequest(BaseModel):
    repo_id: str
    change: str = Field(min_length=3, max_length=1000)
