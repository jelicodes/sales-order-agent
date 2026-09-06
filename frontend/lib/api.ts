export interface ToolOutput {
  type: "tool_output";
  tool_type: string;
  data: Record<string, unknown>;
}

export interface TextDelta {
  type: "text_delta";
  content: string;
}

export interface SessionInfo {
  type: "session";
  session_id: string;
  request_id: string;
}

export interface StreamDone {
  type: "done";
}

export type StreamEvent = ToolOutput | TextDelta | SessionInfo | StreamDone;

export interface StreamCallbacks {
  onToolOutput: (toolType: string, data: Record<string, unknown>) => void;
  onTextDelta: (content: string) => void;
  onSession: (sessionId: string, requestId: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function streamChat(
  message: string,
  sessionId: string,
  callbacks: StreamCallbacks
): Promise<AbortController> {
  const controller = new AbortController();

  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
      signal: controller.signal,
    });

    if (!response.ok) {
      callbacks.onError(`HTTP ${response.status}`);
      return controller;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return controller;
    }

    const decoder = new TextDecoder();
    let buffer = "";
    let currentEvent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          const data = line.slice(6);
          dispatchEvent(currentEvent, data, callbacks);
          currentEvent = "";
        } else if (line.trim() === "" && currentEvent) {
          currentEvent = "";
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return controller;
    }
    callbacks.onError(err instanceof Error ? err.message : "Unknown error");
  }

  return controller;
}

function dispatchEvent(
  event: string,
  data: string,
  callbacks: StreamCallbacks
): void {
  switch (event) {
    case "session_info": {
      try {
        const parsed = JSON.parse(data);
        callbacks.onSession(parsed.session_id, parsed.request_id);
      } catch {
        // Skip malformed JSON
      }
      break;
    }
    case "tool_output": {
      try {
        const parsed = JSON.parse(data);
        callbacks.onToolOutput(parsed.type, parsed.data);
      } catch {
        // Skip malformed JSON
      }
      break;
    }
    case "text_delta":
      callbacks.onTextDelta(data);
      break;
    case "hitl_interrupt": {
      try {
        const parsed = JSON.parse(data);
        callbacks.onToolOutput("hitl_interrupt", parsed);
      } catch {
        // Skip malformed JSON
      }
      break;
    }
    case "error": {
      try {
        const parsed = JSON.parse(data);
        callbacks.onError(parsed.message || "Unknown error");
      } catch {
        callbacks.onError("Unknown error");
      }
      break;
    }
    case "stream_end":
      callbacks.onDone();
      break;
  }
}
