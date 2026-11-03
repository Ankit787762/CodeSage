# ============================================================
# PART 1 — IMPORTS
# ============================================================

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)

from app import config
from app import embedder
from app.chunker import chunk_files
from app.ingestion import get_code_files

# ============================================================
# PART 2 — CONNECT TO QDRANT
# ============================================================

client = QdrantClient(
    url=config.QDRANT_URL,
    api_key=config.QDRANT_API_KEY,
    timeout=120,
)

print("Connected to Qdrant Cloud!")


# ============================================================
# PART 3 — CREATE COLLECTION (only if it does not exist)
# ============================================================


def create_collection_if_needed():

    if client.collection_exists(config.COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config=VectorParams(
            size=config.EMBEDDING_SIZE,
            distance=Distance.COSINE,
        ),
    )

    # Index so we can filter search results by repo_id
    client.create_payload_index(
        collection_name=config.COLLECTION_NAME,
        field_name="repo_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    print(f"Created collection: {config.COLLECTION_NAME}")


# ============================================================
# PART 4 — STORE CHUNKS IN QDRANT
# ============================================================


def store_chunks(repo_id, chunks, embeddings):

    create_collection_if_needed()

    points = []

    for i in range(len(chunks)):

        payload = {
            "repo_id": repo_id,
            "file_path": chunks[i]["file_path"],
            "start_line": chunks[i]["start_line"],
            "end_line": chunks[i]["end_line"],
            "content": chunks[i]["content"],
        }

        point = PointStruct(id=str(uuid.uuid4()), vector=embeddings[i], payload=payload)

        points.append(point)

    # Upload 20 points at a time
    for i in range(0, len(points), 20):
        client.upsert(
            collection_name=config.COLLECTION_NAME,
            points=points[i : i + 20],
        )
        print(f"Uploaded {min(i + 20, len(points))} / {len(points)} chunks")


# ============================================================
# PART 5 — SEARCH (only inside one repo)
# ============================================================


def search(repo_id, query_vector, top_k):

    repo_filter = Filter(
        must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
    )

    results = client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=query_vector,
        query_filter=repo_filter,
        limit=top_k,
        with_payload=True,
    ).points

    chunks = []

    for result in results:
        chunks.append(
            {
                "file_path": result.payload["file_path"],
                "start_line": result.payload["start_line"],
                "end_line": result.payload["end_line"],
                "content": result.payload["content"],
                "score": result.score,
            }
        )

    return chunks


# ============================================================
# PART 6 — INDEX A WHOLE REPO
# read files -> chunk -> embed -> store
# ============================================================


def index_repo(repo_id):

    files = get_code_files(repo_id)

    if len(files) == 0:
        raise ValueError("No code files found in this ZIP")

    chunks = chunk_files(files)

    # File path is added to the text, it helps search find the right file
    texts = [chunk["file_path"] + "\n" + chunk["content"] for chunk in chunks]

    embeddings = embedder.embed_texts(texts)

    store_chunks(repo_id, chunks, embeddings)

    return len(files), len(chunks)


# ============================================================
# PART 7 — TEST
# ============================================================

if __name__ == "__main__":

    import sys

    repo_id = sys.argv[1]

    files_count, chunks_count = index_repo(repo_id)
    print(f"Indexed {files_count} files, {chunks_count} chunks")

    question = "how does login work"
    results = search(repo_id, embedder.embed_text(question), config.TOP_K)

    print("\nSearch results:")

    for r in results:
        print(
            f"Score: {r['score']:.3f}  {r['file_path']} lines {r['start_line']}-{r['end_line']}"
        )
