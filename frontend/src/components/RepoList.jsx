// ============================================================
// PART 1 — IMPORTS
// ============================================================

import { useEffect, useState } from "react";

import { deleteRepo, listRepos } from "../api";


// ============================================================
// PART 2 — REPOSITORY LIST
// ============================================================

export default function RepoList({ onOpen }) {

  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  // Load the list when the page opens
  useEffect(() => {
    loadRepos();
  }, []);


  async function loadRepos() {

    try {
      setRepos(await listRepos());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }


  async function handleDelete(repo) {

    if (!window.confirm(`Delete "${repo.name}"? You will need to upload it again.`)) {
      return;
    }

    try {
      await deleteRepo(repo.repo_id);
      setRepos((previous) => previous.filter((r) => r.repo_id !== repo.repo_id));
    } catch (err) {
      setError(err.message);
    }
  }


  return (
    <div className="mt-12">

      <h3 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-500">
        Your repositories
      </h3>

      {loading && <p className="text-sm text-slate-400">Loading...</p>}

      {error && <p className="text-sm text-red-400">{error}</p>}

      {!loading && !error && repos.length === 0 && (
        <p className="text-sm text-slate-500">
          No repositories yet. Upload your first ZIP above.
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">

        {repos.map((repo) => (
          <div
            key={repo.repo_id}
            className="flex items-center rounded-xl border border-slate-800 bg-slate-900 transition hover:border-indigo-500"
          >

            <button
              onClick={() => onOpen(repo)}
              className="min-w-0 flex-1 px-4 py-3 text-left"
            >
              <p className="truncate font-medium">{repo.name}</p>
              <p className="mt-1 text-xs text-slate-400">
                {repo.files_indexed} files · {repo.chunks_indexed} chunks ·{" "}
                {new Date(repo.created * 1000).toLocaleDateString()}
              </p>
            </button>

            <button
              onClick={() => handleDelete(repo)}
              className="px-3 text-xs text-slate-500 hover:text-red-400"
            >
              Delete
            </button>

          </div>
        ))}

      </div>

    </div>
  );
}