# ============================================================
# PART 1 — IMPORTS
# ============================================================

from app import config

# ============================================================
# PART 2 — CHUNK ONE FILE
#
# Split a file into windows of 40 lines with 10 lines overlap,
# so a function cut in the middle still keeps its context.
# ============================================================


def chunk_file(file):

    lines = file["content"].split("\n")
    chunks = []

    step = config.CHUNK_SIZE_LINES - config.CHUNK_OVERLAP_LINES
    start = 0

    while start < len(lines):

        end = min(start + config.CHUNK_SIZE_LINES, len(lines))
        content = "\n".join(lines[start:end])

        # Skip chunks that are only empty lines
        if content.strip():
            chunks.append(
                {
                    "file_path": file["file_path"],
                    "start_line": start + 1,
                    "end_line": end,
                    "content": content,
                }
            )

        if end == len(lines):
            break

        start += step

    return chunks


# ============================================================
# PART 3 — CHUNK ALL FILES
# ============================================================


def chunk_files(files):

    all_chunks = []

    for file in files:
        all_chunks.extend(chunk_file(file))

    return all_chunks


# ============================================================
# PART 4 — TEST
# ============================================================

if __name__ == "__main__":

    import sys
    from app.ingestion import get_code_files

    files = get_code_files(sys.argv[1])
    chunks = chunk_files(files)

    print(f"Files: {len(files)}")
    print(f"Chunks: {len(chunks)}")

    first = chunks[0]
    print(
        f"\nFirst chunk: {first['file_path']} lines {first['start_line']}-{first['end_line']}"
    )
    print(first["content"])
