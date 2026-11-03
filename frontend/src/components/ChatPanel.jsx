// ============================================================
// PART 1 — IMPORTS
// ============================================================

import { useEffect, useRef, useState } from "react";

import { streamRequest } from "../api";
import Message from "./Message";


// ============================================================
// PART 2 — EXAMPLE QUESTIONS
// ============================================================

const EXAMPLES = {
  chat: [
    "Give me an overview of this project",
    "What files are in this project?",
    "Explain the main execution flow",
  ],
  impact: [
    "Rename the main calculation function",
    "Change the formula used in the main calculation",
  ],
};


// ============================================================
// PART 3 — CHAT PANEL
// ============================================================

export default function ChatPanel({ repo }) {

  const [mode, setMode] = useState("chat");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);


  // Scroll to the bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  // Change the last message (the assistant message we are streaming into)
  function updateLast(change) {
    setMessages((previous) => {
      const copy = [...previous];
      copy[copy.length - 1] = change(copy[copy.length - 1]);
      return copy;
    });
  }


  async function send() {

    const text = input.trim();

    if (text.length < 3 || loading) return;

    setInput("");
    setLoading(true);

    // Add the user message and an empty assistant message
    setMessages((previous) => [
      ...previous,
      { role: "user", text },
      { role: "assistant", text: "", status: "Thinking...", sources: [] },
    ]);

    const path = mode === "chat" ? "/chat" : "/impact";

    const body =
      mode === "chat"
        ? { repo_id: repo.repo_id, question: text }
        : { repo_id: repo.repo_id, change: text };

    try {

      await streamRequest(path, body, (event) => {

        if (event.type === "status") {
          updateLast((m) => ({ ...m, status: event.data }));
        }

        if (event.type === "token") {
          updateLast((m) => ({ ...m, text: m.text + event.data, status: "" }));
        }

        if (event.type === "sources") {
          updateLast((m) => ({ ...m, sources: event.data }));
        }

        if (event.type === "error") {
          updateLast((m) => ({ ...m, status: "", error: event.data }));
        }
      });

    } catch (err) {
      updateLast((m) => ({ ...m, status: "", error: err.message }));
    } finally {
      setLoading(false);
    }
  }


  return (
    <div className="mx-auto flex h-full max-w-4xl flex-col px-4">

      {/* Mode switch */}
      <div className="flex gap-2 py-3">
        <button
          onClick={() => setMode("chat")}
          className={`rounded-full px-4 py-1 text-sm ${
            mode === "chat" ? "bg-indigo-600" : "border border-slate-700 text-slate-300"
          }`}
        >
          Ask a question
        </button>
        <button
          onClick={() => setMode("impact")}
          className={`rounded-full px-4 py-1 text-sm ${
            mode === "impact" ? "bg-indigo-600" : "border border-slate-700 text-slate-300"
          }`}
        >
          Impact analysis
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto pb-4">

        {messages.length === 0 && (
          <div className="mt-10 text-center">
            <p className="mb-4 text-slate-400">
              {mode === "chat"
                ? "Ask anything about your codebase."
                : "Describe a code change and see what it could affect."}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {EXAMPLES[mode].map((example) => (
                <button
                  key={example}
                  onClick={() => setInput(example)}
                  className="rounded-full border border-slate-700 px-3 py-1 text-sm text-slate-300 hover:bg-slate-800"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={(event) => { event.preventDefault(); send(); }}
        className="flex gap-2 border-t border-slate-800 py-3"
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={
            mode === "chat"
              ? "Ask about your codebase..."
              : "Describe a change, e.g. Change the EMI formula to include a processing fee"
          }
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm outline-none focus:border-indigo-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-50"
        >
          {loading ? "Working..." : "Send"}
        </button>
      </form>

    </div>
  );
}