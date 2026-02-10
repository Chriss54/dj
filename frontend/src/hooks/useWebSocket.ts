"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { ProgressUpdate, PipelineStage } from "@/lib/types";
import { getWsUrl } from "@/lib/api";

export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const [stage, setStage] = useState<PipelineStage>("idle");
  const [message, setMessage] = useState("");
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocket(getWsUrl(sessionId));
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data: ProgressUpdate = JSON.parse(event.data);
        if (data.type === "progress") {
          setStage(data.stage);
          setMessage(data.message);
          setProgress(data.progress);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [sessionId]);

  const reset = useCallback(() => {
    setStage("idle");
    setMessage("");
    setProgress(0);
  }, []);

  return { stage, message, progress, reset };
}
