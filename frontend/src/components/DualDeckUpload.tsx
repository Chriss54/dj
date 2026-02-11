"use client";

import { useCallback, useState } from "react";
import { UploadResult } from "@/lib/types";
import { uploadSong } from "@/lib/api";

interface DualDeckUploadProps {
  onUploadComplete: (deck: "a" | "b", result: UploadResult, originalFilename: string) => void;
  onRemove: (deck: "a" | "b") => void;
  onSwap: () => void;
  uploadedFilenameA: string | null;
  uploadedFilenameB: string | null;
  originalFilenameA: string | null;
  originalFilenameB: string | null;
}

function DeckUpload({
  deck,
  label,
  displayName,
  onComplete,
  onRemove,
  uploadedFilename,
}: {
  deck: "a" | "b";
  label: string;
  displayName: string | null;
  onComplete: (result: UploadResult, originalFilename: string) => void;
  onRemove: () => void;
  uploadedFilename: string | null;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  // Use parent-controlled filename for display (supports external reset)
  const filename = uploadedFilename;
  const [localFilename, setLocalFilename] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setUploading(true);
      setLocalFilename(file.name);
      try {
        const result = await uploadSong(deck, file);
        onComplete(result, file.name);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
        setLocalFilename(null);
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
      <div className="mb-1">
        <div className="text-lg font-bold text-zinc-300">
          {displayName || label}
        </div>
        {displayName && (
          <div className="text-[10px] text-zinc-500 uppercase tracking-wider">{label}</div>
        )}
      </div>

      {uploading ? (
        <div className="flex items-center justify-center gap-2 text-indigo-400">
          <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Analyzing {localFilename}...</span>
        </div>
      ) : filename ? (
        <div className="flex items-center justify-center gap-2 text-green-400 text-sm">
          <span>{filename}</span>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onRemove(); }}
            className="w-5 h-5 flex items-center justify-center rounded-full bg-zinc-700 hover:bg-red-500/80 text-zinc-400 hover:text-white transition-colors text-xs leading-none"
            title="Remove song"
          >
            ✕
          </button>
        </div>
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

export default function DualDeckUpload({ onUploadComplete, onRemove, onSwap, uploadedFilenameA, uploadedFilenameB, originalFilenameA, originalFilenameB }: DualDeckUploadProps) {
  // Strip extension for display name
  const stripExt = (name: string | null) => name ? name.replace(/\.[^.]+$/, "") : null;

  const bothUploaded = uploadedFilenameA !== null && uploadedFilenameB !== null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-4 items-center">
      <DeckUpload deck="a" label="Song A" displayName={stripExt(originalFilenameA)} onComplete={(r, name) => onUploadComplete("a", r, name)} onRemove={() => onRemove("a")} uploadedFilename={uploadedFilenameA} />
      {bothUploaded ? (
        <button
          type="button"
          onClick={onSwap}
          className="w-10 h-10 flex items-center justify-center rounded-full bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-400 hover:text-white transition-colors"
          title="Swap songs"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </button>
      ) : (
        <div className="hidden md:block" />
      )}
      <DeckUpload deck="b" label="Song B" displayName={stripExt(originalFilenameB)} onComplete={(r, name) => onUploadComplete("b", r, name)} onRemove={() => onRemove("b")} uploadedFilename={uploadedFilenameB} />
    </div>
  );
}
