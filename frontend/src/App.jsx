// ============================================================
// PART 1 — IMPORTS
// ============================================================

import { useState } from "react";

import HomePage from "./components/HomePage";
import ChatPanel from "./components/ChatPanel";


// ============================================================
// PART 2 — APP
//
// No repo selected -> home page (upload + your repositories)
// Repo selected    -> chat screen
// ============================================================

export default function App() {

  const [repo, setRepo] = useState(null);

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">

      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-3">

        <h1 className="text-lg font-semibold">CodeSage</h1>

        {repo && (
          <div className="flex items-center gap-3 text-sm">
            <span className="rounded bg-emerald-900/50 px-2 py-1 text-emerald-300">
              {repo.name} · {repo.files_indexed} files · {repo.chunks_indexed} chunks
            </span>
            <button
              onClick={() => setRepo(null)}
              className="rounded border border-slate-700 px-3 py-1 hover:bg-slate-800"
            >
              All repositories
            </button>
          </div>
        )}

      </header>

      <main className="flex-1 overflow-hidden">
        {repo ? <ChatPanel repo={repo} /> : <HomePage onOpen={setRepo} />}
      </main>

    </div>
  );
}