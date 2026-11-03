# ============================================================
# PART 1 — IMPORTS
# ============================================================

import os

from app import config
from app import rag
from app.ingestion import get_code_files

MAX_TOOL_CHARS = 6000


# ============================================================
# PART 2 — TOOL 1: SEARCH CODE (semantic search)
# ============================================================


def search_code(repo_id, query):

    chunks = rag.retrieve(repo_id, query)

    sources = []

    for chunk in chunks:
        sources.append(
            {
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
            }
        )

    return rag.format_chunks(chunks), sources


# ============================================================
# PART 3 — TOOL 2: READ FILE (first 300 lines)
# ============================================================


def read_file(repo_id, file_path):

    repo_path = os.path.abspath(os.path.join(config.REPOS_DIR, repo_id))
    full_path = os.path.abspath(os.path.join(repo_path, file_path))

    # Safety check: only files inside this repo can be read
    if not full_path.startswith(repo_path + os.sep) or not os.path.isfile(full_path):
        return "File not found: " + file_path, []

    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().split("\n")

    shown = lines[:300]
    numbered = [f"{i + 1}: {line}" for i, line in enumerate(shown)]

    sources = [{"file_path": file_path, "start_line": 1, "end_line": len(shown)}]

    return "\n".join(numbered), sources


# ============================================================
# PART 4 — TOOL 3: FIND REFERENCES (where is a name used)
# ============================================================


def find_references(repo_id, symbol):

    files = get_code_files(repo_id)

    matches = []
    sources = []

    for file in files:

        for number, line in enumerate(file["content"].split("\n"), start=1):

            if symbol.lower() in line.lower():
                matches.append(f"{file['file_path']}:{number}: {line.strip()}")
                sources.append(
                    {
                        "file_path": file["file_path"],
                        "start_line": number,
                        "end_line": number,
                    }
                )

        if len(matches) >= 30:
            break

    if len(matches) == 0:
        return "No references found for: " + symbol, []

    return "\n".join(matches[:30]), sources[:30]


# ============================================================
# PART 5 — TOOL 4: LIST FILES (project structure)
# ============================================================


def list_files(repo_id):

    files = get_code_files(repo_id)

    paths = [file["file_path"] for file in files]

    return "\n".join(paths[:200]), []


# ============================================================
# PART 6 — TOOL DESCRIPTIONS (so Groq knows what tools exist)
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Semantic search over the codebase. Use it to find code related to a topic, feature or question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for, for example 'user login authentication'",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a full file (first 300 lines) when a search result is not enough.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path exactly as shown in search results, for example 'src/auth.js'",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_references",
            "description": "Find every line where a function, class or variable name is used. Use it for impact analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Exact name, for example 'createOrder'",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all code files in the project to understand its structure.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ============================================================
# PART 7 — RUN A TOOL BY NAME
# ============================================================


def run_tool(name, args, repo_id):

    # repo_id is added by us, the model cannot touch another repo
    if name == "search_code":
        text, sources = search_code(repo_id, args["query"])

    elif name == "read_file":
        text, sources = read_file(repo_id, args["file_path"])

    elif name == "find_references":
        text, sources = find_references(repo_id, args["symbol"])

    elif name == "list_files":
        text, sources = list_files(repo_id)

    else:
        return "Unknown tool: " + name, []

    return text[:MAX_TOOL_CHARS], sources


# ============================================================
# PART 8 — TEST
# ============================================================

if __name__ == "__main__":

    import sys

    repo_id = sys.argv[1]

    text, sources = list_files(repo_id)
    print("Files in repo:")
    print(text)

    text, sources = find_references(repo_id, "import")
    print("\nReferences to 'import':")
    print(text[:500])
