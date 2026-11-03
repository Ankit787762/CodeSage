# ============================================================
# PART 1 — IMPORTS
# ============================================================

import json
import os
import shutil
import zipfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app import config
from app.agent import run_agent
from app.ingestion import get_code_files, save_and_extract_zip
from app.schemas import ChatRequest, ImpactRequest, RepoInfo, UploadResponse
from app.vector_store import count_chunks, delete_repo_chunks, index_repo

router = APIRouter()


# ============================================================
# PART 2 — HELPER FUNCTIONS
# ============================================================


def check_repo(repo_id):

    repo_path = os.path.join(config.REPOS_DIR, repo_id)

    if not repo_id.isalnum() or not os.path.isdir(repo_path):
        raise HTTPException(status_code=404, detail="Repository not found")


def remove_repo(repo_id):

    # Delete chunks from Qdrant, then the extracted files
    try:
        delete_repo_chunks(repo_id)
    except Exception as error:
        print(f"Could not delete chunks of {repo_id}: {error}")

    shutil.rmtree(os.path.join(config.REPOS_DIR, repo_id), ignore_errors=True)


def get_repo_name(repo_id):

    # Most ZIPs contain one root folder, we use its name
    repo_path = os.path.join(config.REPOS_DIR, repo_id)
    items = os.listdir(repo_path)

    if len(items) == 1 and os.path.isdir(os.path.join(repo_path, items[0])):
        return items[0]

    return repo_id


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

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="This is not a valid ZIP file")

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    try:
        files_count, chunks_count = index_repo(repo_id)

    except ValueError as error:
        remove_repo(repo_id)
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        # Indexing failed halfway, clean everything so the list stays correct
        remove_repo(repo_id)
        raise HTTPException(status_code=500, detail="Indexing failed: " + str(error))

    return UploadResponse(
        repo_id=repo_id,
        files_indexed=files_count,
        chunks_indexed=chunks_count,
    )


# ============================================================
# PART 4 — LIST REPOSITORIES
#
# A repo is shown only if its chunks exist in Qdrant,
# so broken or half uploaded repos are hidden.
# ============================================================


@router.get("/repos", response_model=list[RepoInfo])
def list_repos():

    repos = []

    for repo_id in os.listdir(config.REPOS_DIR):

        repo_path = os.path.join(config.REPOS_DIR, repo_id)

        if not os.path.isdir(repo_path):
            continue

        chunks = count_chunks(repo_id)

        if chunks == 0:
            continue

        repos.append(
            {
                "repo_id": repo_id,
                "name": get_repo_name(repo_id),
                "files_indexed": len(get_code_files(repo_id)),
                "chunks_indexed": chunks,
                "created": os.path.getctime(repo_path),
            }
        )

    # Newest first
    repos.sort(key=lambda repo: repo["created"], reverse=True)

    return repos


# ============================================================
# PART 5 — DELETE A REPOSITORY
# ============================================================


@router.delete("/repos/{repo_id}")
def delete_repo(repo_id: str):

    check_repo(repo_id)

    remove_repo(repo_id)

    return {"deleted": repo_id}


# ============================================================
# PART 6 — STREAM EVENTS TO THE FRONTEND (SSE format)
# ============================================================


def make_stream(repo_id, question, mode):

    try:
        for event in run_agent(repo_id, question, mode):
            yield "data: " + json.dumps(event) + "\n\n"

    except Exception as error:
        yield "data: " + json.dumps({"type": "error", "data": str(error)}) + "\n\n"

    yield "data: " + json.dumps({"type": "done", "data": ""}) + "\n\n"


# ============================================================
# PART 7 — CHAT ENDPOINT
# ============================================================


@router.post("/chat")
def chat(request: ChatRequest):

    check_repo(request.repo_id)

    return StreamingResponse(
        make_stream(request.repo_id, request.question, "chat"),
        media_type="text/event-stream",
    )


# ============================================================
# PART 8 — IMPACT ANALYSIS ENDPOINT
# ============================================================


@router.post("/impact")
def impact(request: ImpactRequest):

    check_repo(request.repo_id)

    question = "Proposed change: " + request.change

    return StreamingResponse(
        make_stream(request.repo_id, question, "impact"),
        media_type="text/event-stream",
    )
