// ============================================================
// PART 1 — SETTINGS
// ============================================================

const API_URL = "http://127.0.0.1:8000";


// ============================================================
// PART 2 — UPLOAD ZIP
// ============================================================

export async function uploadZip(file) {

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === "string" ? error.detail : "Upload failed");
  }

  return response.json();
}


// ============================================================
// PART 3 — STREAM CHAT / IMPACT
//
// The backend sends events like:   data: {"type": "token", "data": "..."}
// We read the stream and call onEvent() for every event.
// ============================================================

export async function streamRequest(path, body, onEvent) {

  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === "string" ? error.detail : "Request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {

    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Events are separated by a blank line
    const parts = buffer.split("\n\n");
    buffer = parts.pop();

    for (const part of parts) {
      if (part.startsWith("data: ")) {
        onEvent(JSON.parse(part.slice(6)));
      }
    }
  }
}

// ============================================================
// PART 4 — LIST AND DELETE REPOSITORIES
// ============================================================

export async function listRepos() {

  const response = await fetch(`${API_URL}/repos`);

  if (!response.ok) {
    throw new Error("Could not load repositories");
  }

  return response.json();
}


export async function deleteRepo(repoId) {

  const response = await fetch(`${API_URL}/repos/${repoId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Could not delete repository");
  }
}