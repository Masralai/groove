"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import EmptyState from "@/components/EmptyState";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  sql?: string;
  isLoading?: boolean;
  isError?: boolean;
}

type ViewMode = "sidebar" | "full";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [visibleSql, setVisibleSql] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("sidebar");
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const recentQueries = [
    { text: "Show campaigns with highest spend", time: "10:30 AM" },
    { text: "What was my CTR last week?", time: "3:15 PM" },
    { text: "Compare Facebook vs Instagram performance", time: "9:45 AM" },
  ];

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
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage.content }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data?.message || data?.detail || `Server error (${response.status})`;
        console.error("[Chat] API error:", { status: response.status, error: data });
        throw new Error(errorMsg);
      }

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

  const SQLBlock = ({ sql, id }: { sql: string; id: string }) => {
    const isVisible = visibleSql === id;

    return (
      <div className="mt-3 border border-cloud-border rounded-md overflow-hidden">
        <button
          onClick={() => setVisibleSql(isVisible ? null : id)}
          className="w-full flex items-center justify-between px-3 py-2 bg-cloud-gray/50 text-xs font-medium text-slate-text hover:bg-cloud-gray/70 transition-colors"
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
          <div id={`sql-content-${id}`} className="p-3 bg-midnight-ink/5">
            <div className="flex items-center justify-between mb-2">
              <button
                onClick={() => navigator.clipboard.writeText(sql)}
                className="text-xs text-plasma-teal-gradient hover:underline flex items-center space-x-1"
                aria-label="Copy SQL to clipboard"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5a2 2 0 012-2h4a2 2 0 012 2v2a2 2 0 01-2 2h-4a2 2 0 01-2-2V5z" />
                </svg>
                <span>Copy</span>
              </button>
            </div>
            <pre className="text-xs font-mono text-midnight-ink overflow-x-auto whitespace-pre-wrap">
              <code>{sql}</code>
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {viewMode === "sidebar" && (
        <aside className="hidden md:flex w-64 bg-canvas-white border-r border-cloud-border flex-col shrink-0">
          <div className="p-6 border-b border-cloud-border">
            <h2 className="text-sm font-semibold text-midnight-ink uppercase tracking-wider">
              Recent Queries
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {recentQueries.map((query, index) => (
              <button
                key={index}
                onClick={() => {
                  setInputValue(query.text);
                  inputRef.current?.focus();
                }}
                className="w-full text-left p-3 bg-cloud-gray/50 rounded-md hover:bg-cloud-gray/80 transition-colors group"
                aria-label={`Load query: ${query.text}`}
              >
                <p className="text-sm font-medium text-midnight-ink line-clamp-2 group-hover:text-plasma-teal-gradient transition-colors">
                  {query.text}
                </p>
                <p className="text-xs text-slate-text mt-1">{query.time}</p>
              </button>
            ))}
          </div>
          <div className="p-4 border-t border-cloud-border">
            <button
              onClick={() => setViewMode("full")}
              className="w-full text-sm text-slate-text hover:text-midnight-ink transition-colors flex items-center justify-center space-x-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
              <span>Expand</span>
            </button>
          </div>
        </aside>
      )}

      {/* Mobile bottom sheet trigger */}
      <button
        onClick={() => setShowMobileSidebar(true)}
        className="fixed bottom-4 right-4 z-30 md:hidden w-12 h-12 bg-gradient-to-br from-[#19a05f] to-[#0d7f8c] text-white rounded-full shadow-lg flex items-center justify-center"
        aria-label="Show recent queries"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Mobile bottom sheet */}
      {showMobileSidebar && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setShowMobileSidebar(false)} />
          <div className="absolute bottom-0 inset-x-0 bg-canvas-white rounded-t-2xl shadow-xl max-h-[60vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-cloud-border">
              <h2 className="text-sm font-semibold text-midnight-ink uppercase tracking-wider">Recent Queries</h2>
              <button
                onClick={() => setShowMobileSidebar(false)}
                className="w-8 h-8 flex items-center justify-center rounded-full text-slate-text hover:bg-cloud-gray/50 transition-colors"
                aria-label="Close"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {recentQueries.length === 0 ? (
                <p className="text-sm text-slate-text text-center py-8">No recent queries yet.</p>
              ) : (
                recentQueries.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setInputValue(query.text);
                      setShowMobileSidebar(false);
                      inputRef.current?.focus();
                    }}
                    className="w-full text-left p-3 bg-cloud-gray/50 rounded-md hover:bg-cloud-gray/80 transition-colors"
                  >
                    <p className="text-sm font-medium text-midnight-ink line-clamp-2">{query.text}</p>
                    <p className="text-xs text-slate-text mt-1">{query.time}</p>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}

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
              description='Ask questions like "What was my top performing campaign last month?" or "Show me CTR trends for Q2."'
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
                        ? "border border-red-300"
                        : ""
                    } ${
                      message.isUser
                        ? "bg-gradient-to-br from-[#19a05f] to-[#0d7f8c] text-white rounded-2xl rounded-br-sm"
                        : message.isError
                        ? "bg-red-50 text-red-800 rounded-2xl rounded-bl-sm"
                        : "bg-cloud-gray text-midnight-ink rounded-2xl rounded-bl-sm"
                    } px-5 py-3.5`}
                  >
                    {message.isLoading ? (
                      <div className="flex items-center space-x-3 py-1" aria-label="Loading response">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-slate-text rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                          <div className="w-2 h-2 bg-slate-text rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                          <div className="w-2 h-2 bg-slate-text rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                        <span className="text-sm text-slate-text">Analyzing your data...</span>
                      </div>
                    ) : (
                      <>
                        <p className="text-base leading-relaxed whitespace-pre-wrap break-words">
                          {message.content}
                        </p>
                        {message.sql && (
                          <SQLBlock sql={message.sql} id={message.id} />
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
          className="flex items-center space-x-4 px-10 py-4 bg-canvas-white border-t border-cloud-border"
        >
          {viewMode === "sidebar" && (
            <button
              type="button"
              onClick={() => setViewMode("full")}
              className="hidden md:flex items-center justify-center w-10 h-10 rounded-full border border-cloud-border text-slate-text hover:bg-cloud-gray/50 transition-colors"
              aria-label="Expand sidebar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
          )}
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
                <div className="w-5 h-5 border-2 border-cloud-border border-t-plasma-teal-gradient rounded-full animate-spin" role="status" aria-label="Loading" />
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