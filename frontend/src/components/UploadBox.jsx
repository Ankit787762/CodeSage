// ============================================================
// PART 1 — IMPORTS
// ============================================================

import { useState } from "react";

import { uploadZip } from "../api";


// ============================================================
// PART 2 — UPLOAD BOX
// ============================================================

export default function UploadBox({ onUploaded }) {

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);


  async function handleFile(file) {

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".zip")) {
      setError("Please choose a .zip file");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data = await uploadZip(file);
      onUploaded({ ...data, name: file.name.replace(".zip", "") });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }


  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    handleFile(event.dataTransfer.files[0]);
  }


  return (
    <div>

      <label
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex w-full cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition ${
          dragging
            ? "border-indigo-400 bg-indigo-950/40"
            : "border-slate-700 hover:border-slate-500"
        }`}
      >
        {loading ? (
          <>
            <p className="animate-pulse text-lg">Indexing your repository...</p>
            <p className="mt-2 text-sm text-slate-400">
              Extracting files, chunking, creating embeddings. This can take up to a minute.
            </p>
          </>
        ) : (
          <>
            <p className="text-lg">Drop your .zip here, or click to choose</p>
            <p className="mt-2 text-sm text-slate-400">Max 50 MB</p>
          </>
        )}

        <input
          type="file"
          accept=".zip"
          className="hidden"
          disabled={loading}
          onChange={(event) => handleFile(event.target.files[0])}
        />
      </label>

      {error && <p className="mt-4 text-center text-sm text-red-400">{error}</p>}

    </div>
  );
}