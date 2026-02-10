"use client";

import { useCallback, useState } from "react";
import { UploadResult } from "@/lib/types";
import { uploadSong } from "@/lib/api";

interface DualDeckUploadProps {
  onUploadComplete: (deck: "a" | "b", result: UploadResult) => void;
}

function DeckUpload({
  deck,
  label,
  onComplete,
}: {
  deck: "a" | "b";
  label: string;
  onComplete: (result: UploadResult) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [filename, setFilename] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setUploading(true);
      setFilename(file.name);
      try {
        const result = await uploadSong(deck, file);
        onComplete(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
        setFilename(null);
      } finally {
        setUploading(false);
      }
    },
    [deck, onComplete],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const onFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
      className={`
        relative border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer
        ${isDragging ? "border-indigo-500 bg-indigo-500/10" : "border-zinc-700 hover:border-zinc-500 bg-zinc-900/50"}
        ${filename ? "border-green-500/50 bg-green-500/5" : ""}
      `}
    >
      <input
        type="file"
        accept=".mp3,.wav,.flac,.ogg,.m4a"
        onChange={onFileSelect}
        className="absolute inset-0 opacity-0 cursor-pointer"
      />
      <div className="text-lg font-bold text-zinc-300 mb-1">{label}</div>

      {uploading ? (
        <div className="flex items-center justify-center gap-2 text-indigo-400">
          <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Analyzing {filename}...</span>
        </div>
      ) : filename ? (
        <div className="text-green-400 text-sm">{filename}</div>
      ) : (
        <div className="text-zinc-500 text-sm">
          Drag & drop or click to select<br />
          MP3, WAV, FLAC, OGG, M4A (max 50MB)
        </div>
      )}

      {error && <div className="text-red-400 text-sm mt-2">{error}</div>}
    </div>
  );
}

export default function DualDeckUpload({ onUploadComplete }: DualDeckUploadProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <DeckUpload deck="a" label="Song A" onComplete={(r) => onUploadComplete("a", r)} />
      <DeckUpload deck="b" label="Song B" onComplete={(r) => onUploadComplete("b", r)} />
    </div>
  );
}
