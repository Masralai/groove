"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import EmptyState from "@/components/EmptyState";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  sql?: string;
  data?: Record<string, unknown>[];
  isLoading?: boolean;
  isError?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [visibleSql, setVisibleSql] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isUser: true,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    const loadingMessage: Message = {
      id: Date.now().toString() + "-loading",
      content: "",
      isUser: false,
      isLoading: true,
    };
    setMessages((prev) => [...prev, loadingMessage]);

    try {
      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage.content }),
      });

      if (!response.ok) {
        let errorMsg = `Server error (${response.status})`;
        try {
          const errData = await response.json();
          errorMsg = errData?.message || errData?.detail || errorMsg;
          console.error("[Chat] API error:", { status: response.status, error: errData });
        } catch {
          console.error("[Chat] Non-JSON error response:", response.status, response.statusText);
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();

      setMessages((prev) =>
        prev.filter((msg) => msg.id !== loadingMessage.id)
      );

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString() + "-response",
          content: data.answer || "No response from the server.",
          isUser: false,
          sql: data.sql,
          data: data.data,
        },
      ]);
    } catch (err) {
      console.error("[Chat] Request failed:", err);
      setMessages((prev) =>
        prev.filter((msg) => msg.id !== loadingMessage.id)
      );
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString() + "-error",
          content:
            err instanceof Error
              ? err.message
              : "An unexpected error occurred. Please try again.",
          isUser: false,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const DataTable = ({ data }: { data: Record<string, unknown>[] }) => {
    if (!data.length) return null;
    const cols = Object.keys(data[0]);
    return (
      <div className="mt-3 overflow-x-auto border border-edge rounded-md">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="bg-elevated/50">
              {cols.map((col) => (
                <th key={col} className="px-3 py-2 text-left text-muted font-medium uppercase tracking-wider whitespace-nowrap">
                  {col.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-edge">
            {data.map((row, i) => (
              <tr key={i} className="hover:bg-elevated/30">
                {cols.map((col) => (
                  <td key={col} className="px-3 py-2 text-cream whitespace-nowrap">
                    {String(row[col] ?? "\u2014")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const SQLBlock = ({ sql, id }: { sql: string; id: string }) => {
    const isVisible = visibleSql === id;

    return (
      <div className="mt-3 border border-edge rounded-md overflow-hidden">
        <button
          onClick={() => setVisibleSql(isVisible ? null : id)}
          className="w-full flex items-center justify-between px-3 py-2 bg-elevated/50 text-xs font-medium text-muted hover:bg-elevated/70 transition-colors"
          aria-expanded={isVisible}
          aria-controls={`sql-content-${id}`}
        >
          <span>Generated SQL</span>
          <svg
            className={`w-3 h-3 transition-transform duration-200 ${isVisible ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isVisible && (
          <div id={`sql-content-${id}`} className="p-3 bg-deep/50">
            <div className="flex items-center justify-between mb-2">
              <button
                onClick={() => navigator.clipboard.writeText(sql)}
                className="text-xs text-amber hover:underline flex items-center space-x-1"
                aria-label="Copy SQL to clipboard"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5a2 2 0 012-2h4a2 2 0 012 2v2a2 2 0 01-2 2h-4a2 2 0 01-2-2V5z" />
                </svg>
                <span>Copy</span>
              </button>
            </div>
            <pre className="text-xs font-mono text-cream overflow-x-auto whitespace-pre-wrap">
              <code>{sql}</code>
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      <div className="flex-1 flex flex-col min-w-0">
        <div
          id="chat-messages"
          className="flex-1 overflow-y-auto"
          role="log"
          aria-label="Chat messages"
          aria-live="polite"
        >
          {messages.length === 0 ? (
            <EmptyState
              variant="chat"
              title="Ask about your ad data"
              description='Ask questions like "What was my top performing campaign of all time?" or "What is the average CTR?"'
            />
          ) : (
            <div className="max-w-3xl mx-auto px-10 py-8 space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] sm:max-w-[75%] ${
                      message.isLoading
                        ? "animate-pulse"
                        : message.isError
                        ? "border border-coral/40"
                        : ""
                    } ${
                      message.isUser
                        ? "bg-gradient-to-br from-amber to-amber-deep text-deep rounded-2xl rounded-br-sm"
                        : message.isError
                        ? "bg-coral/10 text-coral rounded-2xl rounded-bl-sm"
                        : "bg-surface text-cream rounded-2xl rounded-bl-sm border border-edge"
                    } px-5 py-3.5`}
                  >
                    {message.isLoading ? (
                      <div className="flex items-center space-x-3 py-1" aria-label="Loading response">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-amber rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                          <div className="w-2 h-2 bg-amber rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                          <div className="w-2 h-2 bg-amber rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                        <span className="text-sm text-muted">Analyzing your data...</span>
                      </div>
                    ) : (
                      <>
                        <p className="text-base leading-relaxed whitespace-pre-wrap break-words">
                          {message.content}
                        </p>
                        {message.sql && (
                          <SQLBlock sql={message.sql} id={message.id} />
                        )}
                        {message.data && message.data.length > 0 && (
                          <DataTable data={message.data} />
                        )}
                      </>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex items-center space-x-4 px-10 py-4 bg-deep/80 backdrop-blur-lg border-t border-edge"
        >
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask about your Meta Ads data..."
              className="input pr-12"
              aria-label="Type your question about Meta Ads data"
              disabled={isLoading}
            />
            {isLoading && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <div className="w-5 h-5 border-2 border-edge border-t-amber rounded-full animate-spin" role="status" aria-label="Loading" />
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className={`btn-primary min-w-[80px] ${
              !inputValue.trim() || isLoading
                ? "opacity-50 cursor-not-allowed"
                : ""
            }`}
            aria-label="Send message"
          >
            {isLoading ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
