// ============================================================
// PART 1 — IMPORTS
// ============================================================

import UploadBox from "./UploadBox";
import RepoList from "./RepoList";


// ============================================================
// PART 2 — WHAT CODESAGE CAN DO (shown under the heading)
// ============================================================

const FEATURES = [
  { title: "Ask questions", text: "Where is login implemented? How does checkout work?" },
  { title: "Execution flow", text: "Follow a request from the UI to the database." },
  { title: "Impact analysis", text: "See what a code change could break." },
];


// ============================================================
// PART 3 — HOME PAGE
// ============================================================

export default function HomePage({ onOpen }) {

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-4 py-12">

        <h2 className="text-center text-4xl font-bold">
          Understand any <span className="text-indigo-400">codebase</span>
        </h2>

        <p className="mb-8 mt-3 text-center text-slate-400">
          Upload a ZIP of your project and ask questions in plain English.
        </p>

        <div className="mb-8 grid gap-3 sm:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"
            >
              <p className="text-sm font-medium text-indigo-300">{feature.title}</p>
              <p className="mt-1 text-xs text-slate-400">{feature.text}</p>
            </div>
          ))}
        </div>

        <UploadBox onUploaded={onOpen} />

        <RepoList onOpen={onOpen} />

      </div>
    </div>
  );
}