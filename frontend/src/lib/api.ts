const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function uploadSong(deck: "a" | "b", file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload/${deck}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }

  return res.json();
}

export async function createMix(params: {
  song_a_path: string;
  song_b_path: string;
  transition_start_ms?: number;
  song_b_in_point_ms?: number;
  strategy?: string;
  enable_sfx?: boolean;
  mix_in_key?: boolean;
}) {
  const searchParams = new URLSearchParams();
  searchParams.set("song_a_path", params.song_a_path);
  searchParams.set("song_b_path", params.song_b_path);
  if (params.transition_start_ms !== undefined)
    searchParams.set("transition_start_ms", String(params.transition_start_ms));
  if (params.song_b_in_point_ms !== undefined)
    searchParams.set("song_b_in_point_ms", String(params.song_b_in_point_ms));
  if (params.strategy) searchParams.set("strategy", params.strategy);
  if (params.enable_sfx !== undefined)
    searchParams.set("enable_sfx", String(params.enable_sfx));
  if (params.mix_in_key !== undefined)
    searchParams.set("mix_in_key", String(params.mix_in_key));

  const res = await fetch(`${API_BASE}/mix?${searchParams.toString()}`, {
    method: "POST",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Mix failed");
  }

  return res.json();
}

export function getDownloadUrl(sessionId: string) {
  return `${API_BASE}/download/${sessionId}`;
}

export function getWsUrl(sessionId: string) {
  const wsBase = API_BASE.replace("http", "ws");
  return `${wsBase}/ws/${sessionId}`;
}
