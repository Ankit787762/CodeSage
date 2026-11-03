// ============================================================
// PART 1 — IMPORTS
// ============================================================

import ReactMarkdown from "react-markdown";


// ============================================================
// PART 2 — ONE MESSAGE (user or assistant)
// ============================================================

export default function Message({ message }) {

  // User message
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl bg-indigo-600 px-4 py-2 text-sm">
          {message.text}
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3">

      {message.status && (
        <p className="animate-pulse font-mono text-xs text-slate-400">{message.status}</p>
      )}

      {message.text && (
        <div className="prose prose-sm prose-invert max-w-none">
          <ReactMarkdown>{message.text}</ReactMarkdown>
        </div>
      )}

      {message.error && (
        <p className="text-sm text-red-400">Error: {message.error}</p>
      )}

      {message.sources && message.sources.length > 0 && (
        <div className="mt-4 border-t border-slate-800 pt-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Sources</p>
          <div className="flex flex-wrap gap-2">
            {message.sources.map((source, index) => (
              <span
                key={index}
                className="rounded bg-slate-800 px-2 py-1 font-mono text-xs text-sky-300"
              >
                {source.file_path} : {source.start_line}-{source.end_line}
              </span>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}