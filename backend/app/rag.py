# ============================================================
# PART 1 — IMPORTS
# ============================================================

from groq import Groq

from app import config
from app import embedder
from app import vector_store

# ============================================================
# PART 2 — CONNECT TO GROQ
# ============================================================

groq_client = Groq(api_key=config.GROQ_API_KEY, timeout=60, max_retries=3)


# ============================================================
# PART 3 — RETRIEVE RELEVANT CHUNKS
# ============================================================


def retrieve(repo_id, question):

    # Convert the question into an embedding
    query_vector = embedder.embed_text(question)

    # Search Qdrant for similar chunks
    return vector_store.search(repo_id, query_vector, config.TOP_K)


# ============================================================
# PART 4 — FORMAT CHUNKS AS CONTEXT
# ============================================================


def format_chunks(chunks):

    parts = []

    for chunk in chunks:
        header = f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']})"
        parts.append(header + "\n" + chunk["content"])

    return "\n\n---\n\n".join(parts)


# ============================================================
# PART 5 — STREAM ANSWER FROM GROQ
# ============================================================


def stream_llm(messages):

    stream = groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=config.TEMPERATURE,
        stream=True,
    )

    for chunk in stream:

        if not chunk.choices:
            continue

        piece = chunk.choices[0].delta.content

        if piece:
            yield piece


# ============================================================
# PART 6 — SIMPLE RAG (without agent)
# ============================================================


def answer_with_rag(repo_id, question):

    chunks = retrieve(repo_id, question)
    context = format_chunks(chunks)

    prompt = f"""
Answer the question using only the code provided below.
Mention the file path and line numbers for every point.

Code:
{context}

Question:
{question}

If the answer is not present in the code, say:
"I could not find this in the provided code."
"""

    messages = [{"role": "user", "content": prompt}]

    yield from stream_llm(messages)


# ============================================================
# PART 7 — TEST
# ============================================================

if __name__ == "__main__":

    import sys

    repo_id = sys.argv[1]
    question = sys.argv[2]

    for piece in answer_with_rag(repo_id, question):
        print(piece, end="", flush=True)

    print()
