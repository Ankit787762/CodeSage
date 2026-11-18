# ============================================================
# PART 1 — IMPORTS
# ============================================================

import json

from app import config
from app.rag import groq_client
from app.tools import TOOLS, run_tool

MAX_STEPS = 4
MAX_CONTEXT_CHARS = 20000


# ============================================================
# PART 2 — SYSTEM PROMPTS
# ============================================================

# ============================================================
# PART 2 — SYSTEM PROMPTS (only two)
# ============================================================

CHAT_PROMPT = """
You are CodeSage, an assistant that explains codebases.
You answer using code that was collected from the repository.

Rules:
- Start with a direct answer to the user's question.
- Explain step by step how the code works (execution flow).
- Always mention the file path and line numbers.
- Only use line numbers that appear in the code headers. Never invent line numbers.
- If a part of the code was not shown to you, say so. Do not guess.
- Never invent components, functions, files, or features that do not exist in the repository.
- Distinguish between actual implementation and hypothetical examples or suggestions.
- If the code does not contain the answer, or the question is not about this codebase, reply in one or two short sentences, for example: "I could not find X in this repository." Do not list files, do not describe what was retrieved, and do not add sources.
- Do not repeat the same explanation in multiple sections.
- Keep answers concise but give enough technical detail to explain the code correctly.
- Do not use tables. Use short headings and bullet points.
- Put code in separate fenced code blocks, never inside a list or table.
- If you show code from the repository, copy it exactly as given. Never rewrite it and never add, remove or change comments or lines.
- Use inline code for filenames, functions, variables, and technical terms.
- Do not use LaTeX. Write formulas inside a code block.
- Use plain characters only (normal hyphen -, normal spaces).
"""

IMPACT_PROMPT = """
You are CodeSage, an assistant that does change impact analysis.
You will be given a proposed change and code that was collected from the repository.

A complete impact analysis needs the reference list for the changed name (every line in the repository where the name appears), not only search results.

Answer in this format:
1. A table of affected files with the columns: File, Lines, Why it is affected, Risk (High, Medium or Low).
2. A short checklist of what to update or test.

Rules:
- Only mention files and lines that appear in the code you were given.
- When a reference list is present, every file in it must appear in the table, not only the files from the search results.
- Take line numbers from the reference list when it is present, because they are exact. Never count lines yourself and never invent line numbers.
- Give different risk levels when the risk really differs. The place where something is defined is usually High. Files that only import or call it are Medium or Low, depending on how important they are.
- Do not suggest import paths unless you can see them in the code you were given.
- If the code does not show where something is used, say so. Do not guess.
- Keep every table cell short.
- Put code in separate fenced code blocks, never inside a table.
- Use plain characters only (normal hyphen -, normal spaces).
- Never write the words "reference list" or "code headers" in your answer.
"""

# ============================================================
# PART 3 — REMOVE DUPLICATE SOURCES
# ============================================================


def unique_sources(sources):

    seen = set()
    result = []

    for source in sources:

        key = (source["file_path"], source["start_line"], source["end_line"])

        if key not in seen:
            seen.add(key)
            result.append(source)

    return result[:15]


# ============================================================
# PART 4 — AGENT LOOP
#
# 1. The model asks for a tool -> we run it
# 2. We save every tool result in a list called gathered
# 3. When the model needs no more tools (or steps are over),
#    we make a fresh call with the gathered code and stream
#    the final answer. No tools are given in that last call.
# ============================================================


def run_agent(repo_id, question, mode="chat"):

    if mode == "impact":
        system_prompt = IMPACT_PROMPT
    else:
        system_prompt = CHAT_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    all_sources = []
    gathered = []

    for step in range(MAX_STEPS):

        response = groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=config.TEMPERATURE,
        )

        message = response.choices[0].message

        # No tool needed -> the agent has enough information
        if not message.tool_calls:
            break

        # Save the model's tool request in the conversation
        tool_calls = []

        for call in message.tool_calls:
            tool_calls.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
            )

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": tool_calls,
            }
        )

        # Run every requested tool
        for call in message.tool_calls:

            name = call.function.name

            try:
                args = json.loads(call.function.arguments or "{}")

                yield {"type": "status", "data": f"Using tool: {name} {args}"}

                result_text, sources = run_tool(name, args, repo_id)

                all_sources.extend(sources)
                gathered.append(f"Tool: {name} {args}\n{result_text}")

            except Exception as error:
                result_text = "Tool error: " + str(error)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result_text,
                }
            )

    # If the model used no tool at all, we search once ourselves
    if len(gathered) == 0:

        yield {"type": "status", "data": "Using tool: search_code (automatic)"}

        result_text, sources = run_tool("search_code", {"query": question}, repo_id)

        all_sources.extend(sources)
        gathered.append(f"Tool: search_code\n{result_text}")

    # Final answer: fresh call, plain text context, no tools
    context = "\n\n=====\n\n".join(gathered)[:MAX_CONTEXT_CHARS]

    final_messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"""
{question}

Here is the code collected by the tools:

{context}

Now write the final answer using only this code.
Mention file paths and line numbers. Do not call any tools.
If this code does not answer the question, reply in one or two short sentences saying it was not found in this repository. Do not list files or explain what was retrieved.
""",
        },
    ]

    stream = groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=final_messages,
        temperature=config.TEMPERATURE,
        stream=True,
    )

    answer_text = ""

    for chunk in stream:

        if not chunk.choices:
            continue

        piece = chunk.choices[0].delta.content

        if piece:
            answer_text += piece
            yield {"type": "token", "data": piece}

    # Show only the sources whose file name appears in the answer
    cited = [s for s in all_sources if s["file_path"].split("/")[-1] in answer_text]

    yield {"type": "sources", "data": unique_sources(cited)}


# ============================================================
# PART 5 — TEST
# ============================================================

if __name__ == "__main__":

    import sys

    repo_id = sys.argv[1]
    question = sys.argv[2]

    for event in run_agent(repo_id, question):

        if event["type"] == "status":
            print(f"\n[{event['data']}]")

        elif event["type"] == "token":
            print(event["data"], end="", flush=True)

        elif event["type"] == "sources":
            print("\n\nSources:")
            for s in event["data"]:
                print(f"  {s['file_path']} lines {s['start_line']}-{s['end_line']}")
