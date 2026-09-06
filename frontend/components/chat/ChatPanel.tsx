"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { streamChat } from "@/lib/api";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { ComponentRenderer } from "./ComponentRenderer";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolOutputs?: Array<{ type: string; data: Record<string, unknown> }>;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(
    async (content: string) => {
      if (isStreaming) return;

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
      };

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "",
        toolOutputs: [],
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      const controller = await streamChat(content, sessionId, {
        onSession: (sid) => setSessionId(sid),
        onTextDelta: (delta) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                content: last.content + delta,
              };
            }
            return updated;
          });
        },
        onToolOutput: (toolType, data) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                toolOutputs: [
                  ...(last.toolOutputs || []),
                  { type: toolType, data },
                ],
              };
            }
            return updated;
          });
        },
        onDone: () => setIsStreaming(false),
        onError: () => setIsStreaming(false),
      });

      abortRef.current = controller;
    },
    [isStreaming, sessionId]
  );

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            <p className="text-sm">Selamat datang! Ketik pesan untuk memulai.</p>
          </div>
        )}
        <div className="space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className="space-y-2">
              <ChatBubble role={msg.role}>{msg.content}</ChatBubble>
              {msg.toolOutputs?.map((tool, i) => (
                <ComponentRenderer key={i} type={tool.type} data={tool.data} />
              ))}
            </div>
          ))}
        </div>
      </div>
      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
