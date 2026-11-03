# ============================================================
# PART 1 — IMPORTS AND SETTINGS
# ============================================================

import io
import os
import shutil
import uuid
import zipfile

from app import config

# Folders and files we never want to read
IGNORE_FOLDERS = [
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
]

IGNORE_FILES = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "uv.lock"]

# Only these file types are treated as code
CODE_EXTENSIONS = [
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".html",
    ".css",
    ".json",
    ".md",
    ".txt",
    ".c",
    ".cpp",
    ".php",
    ".rb",
]

MAX_FILE_KB = 200


# ============================================================
# PART 2 — EXTRACT ZIP SAFELY
# ============================================================


def save_and_extract_zip(zip_bytes):

    # Every uploaded repo gets a short random id
    repo_id = str(uuid.uuid4())[:8]
    repo_path = os.path.join(config.REPOS_DIR, repo_id)
    os.makedirs(repo_path)

    max_bytes = config.MAX_ZIP_MB * 1024 * 1024
    total_size = 0

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:

            for member in zf.infolist():

                # Skip ignored folders like node_modules and .git
                parts = member.filename.split("/")
                if any(part in IGNORE_FOLDERS for part in parts):
                    continue

                # Safety check: a file must stay inside the repo folder
                target = os.path.abspath(os.path.join(repo_path, member.filename))
                if not target.startswith(os.path.abspath(repo_path) + os.sep):
                    raise ValueError("Unsafe file path in ZIP")

                # Safety check: total size limit
                total_size += member.file_size
                if total_size > max_bytes:
                    raise ValueError(f"ZIP is too large (max {config.MAX_ZIP_MB} MB)")

                zf.extract(member, repo_path)

    except Exception:
        # Remove the half extracted repo and pass the error on
        shutil.rmtree(repo_path, ignore_errors=True)
        raise

    return repo_id


# ============================================================
# PART 3 — READ ALL CODE FILES OF A REPO
# ============================================================


def get_code_files(repo_id):

    repo_path = os.path.join(config.REPOS_DIR, repo_id)
    files = []

    for folder, subfolders, filenames in os.walk(repo_path):

        # Do not walk into ignored folders
        subfolders[:] = [f for f in subfolders if f not in IGNORE_FOLDERS]

        for name in filenames:

            if name in IGNORE_FILES:
                continue

            extension = os.path.splitext(name)[1].lower()
            if extension not in CODE_EXTENSIONS:
                continue

            full_path = os.path.join(folder, name)
            if os.path.getsize(full_path) > MAX_FILE_KB * 1024:
                continue

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            relative_path = os.path.relpath(full_path, repo_path).replace("\\", "/")

            files.append({"file_path": relative_path, "content": content})

    return files


# ============================================================
# PART 4 — TEST
# ============================================================

if __name__ == "__main__":

    import sys

    with open(sys.argv[1], "rb") as f:
        repo_id = save_and_extract_zip(f.read())

    files = get_code_files(repo_id)

    print(f"Repo ID: {repo_id}")
    print(f"Code files found: {len(files)}")

    for file in files[:10]:
        print(f"  {file['file_path']} ({len(file['content'])} characters)")
