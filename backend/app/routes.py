# ============================================================
# PART 1 — IMPORTS
# ============================================================

import json
import os
import zipfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app import config
from app.agent import run_agent
from app.ingestion import save_and_extract_zip
from app.schemas import ChatRequest, ImpactRequest, UploadResponse
from app.vector_store import index_repo

router = APIRouter()


# ============================================================
# PART 2 — CHECK THAT THE REPO EXISTS
# ============================================================


def check_repo(repo_id):

    repo_path = os.path.join(config.REPOS_DIR, repo_id)

    if not repo_id.isalnum() or not os.path.isdir(repo_path):
        raise HTTPException(status_code=404, detail="Repository not found")


# ============================================================
# PART 3 — UPLOAD ENDPOINT
# ============================================================


@router.post("/upload", response_model=UploadResponse)
def upload(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip file")

    zip_bytes = file.file.read()

    try:
        repo_id = save_and_extract_zip(zip_bytes)
        files_count, chunks_count = index_repo(repo_id)

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="This is not a valid ZIP file")

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return UploadResponse(
        repo_id=repo_id,
        files_indexed=files_count,
        chunks_indexed=chunks_count,
    )


# ============================================================
# PART 4 — STREAM EVENTS TO THE FRONTEND (SSE format)
# ============================================================


def make_stream(repo_id, question, mode):

    try:
        for event in run_agent(repo_id, question, mode):
            yield "data: " + json.dumps(event) + "\n\n"

    except Exception as error:
        yield "data: " + json.dumps({"type": "error", "data": str(error)}) + "\n\n"

    yield "data: " + json.dumps({"type": "done", "data": ""}) + "\n\n"


# ============================================================
# PART 5 — CHAT ENDPOINT
# ============================================================


@router.post("/chat")
def chat(request: ChatRequest):

    check_repo(request.repo_id)

    return StreamingResponse(
        make_stream(request.repo_id, request.question, "chat"),
        media_type="text/event-stream",
    )


# ============================================================
# PART 6 — IMPACT ANALYSIS ENDPOINT
# ============================================================


@router.post("/impact")
def impact(request: ImpactRequest):

    check_repo(request.repo_id)

    question = "Proposed change: " + request.change

    return StreamingResponse(
        make_stream(request.repo_id, question, "impact"),
        media_type="text/event-stream",
    )
