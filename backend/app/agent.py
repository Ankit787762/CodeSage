# ============================================================
# PART 1 — IMPORTS
# ============================================================

import json

from app import config
from app.rag import groq_client
from app.tools import TOOLS, run_tool

MAX_STEPS = 4
MAX_CONTEXT_CHARS = 12000


# ============================================================
# PART 2 — SYSTEM PROMPTS
# ============================================================

CHAT_PROMPT = """
You are CodeSage, an assistant that explains codebases.

Rules:
- Use the tools to find the relevant code before answering. Do not guess.
- Start with search_code. Use read_file if you need more of a file.
- Use at most 3 tool calls, then stop and answer.
- Explain step by step how the code works (execution flow).
- Always mention the file path and line numbers.
- Only use line numbers that appear in the code headers. Never invent line numbers.
- If a part of the code was not shown to you, say so. Do not guess.
- Do not use tables. Use short headings and bullet points.
- Put code in separate fenced code blocks, never inside a list or table.
- Do not use LaTeX. Write formulas inside a code block.
- Use plain characters only (normal hyphen -, normal spaces).
"""

IMPACT_PROMPT = """
You are CodeSage, an assistant that does change impact analysis.

The user will describe a code change. Do this:
1. Use search_code to find the code that will change.
2. Use find_references to find where that function, class or variable is used.
3. Use read_file if you need more detail.
Use at most 4 tool calls, then stop and answer.

Then answer in this format:
- Affected files (file path, line numbers, and why it is affected)
- Risk level for each: High, Medium or Low
- A short checklist of what to update or test

Only mention files that you actually found with the tools.
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
""",
        },
    ]

    stream = groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=final_messages,
        temperature=config.TEMPERATURE,
        stream=True,
    )

    for chunk in stream:

        if not chunk.choices:
            continue

        piece = chunk.choices[0].delta.content

        if piece:
            yield {"type": "token", "data": piece}

    yield {"type": "sources", "data": unique_sources(all_sources)}


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
