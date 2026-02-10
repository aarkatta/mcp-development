'use client';

import { useState, useCallback, useRef } from 'react';
import { Message } from '@/lib/types';

const MCP_CLIENT_URL = process.env.NEXT_PUBLIC_MCP_CLIENT_URL || 'http://localhost:9080';
const STREAM_URL = `${MCP_CLIENT_URL.replace(/\/chat$/, '')}/chat/stream`;

function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  search_adverse_events: 'Searching adverse events',
  get_serious_adverse_events: 'Fetching serious adverse events',
  get_drug_label: 'Looking up drug labeling',
  search_drug_labels: 'Searching drug labels',
  search_recalls: 'Searching drug recalls',
  get_recent_drug_recalls: 'Fetching recent recalls',
  get_recalls_by_classification: 'Fetching recalls by classification',
  get_critical_recalls: 'Fetching critical recalls',
  search_drug_shortages: 'Searching drug shortages',
  get_current_drug_shortages: 'Checking current shortages',
  search_shortages_by_manufacturer: 'Searching shortages by manufacturer',
};

function getToolDisplayName(toolName: string): string {
  return TOOL_DISPLAY_NAMES[toolName] || `Running ${toolName}`;
}

interface SSEEvent {
  event: string;
  data: string;
}

function parseSSEEvents(text: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  // SSE events are separated by blank lines: \n\n, \r\n\r\n, or \r\r
  const blocks = text.split(/\r?\n\r?\n/);

  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed) continue;

    let eventType = 'message';
    let data = '';

    for (const line of trimmed.split(/\r?\n/)) {
      if (line.startsWith('event:')) {
        eventType = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        data = line.slice(5).trim();
      }
      // Ignore comment lines (: ping) and other fields
    }

    if (data) {
      events.push({ event: eventType, data });
    }
  }

  return events;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Abort any in-flight stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    const assistantMessageId = generateId();

    // Add user message and empty streaming assistant message
    setMessages((prev) => [
      ...prev,
      userMessage,
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      },
    ]);
    setIsLoading(true);

    try {
      const response = await fetch(STREAM_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content.trim(),
          session_id: sessionIdRef.current,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Only process complete SSE events (terminated by \r\n\r\n or \n\n)
        // Normalize \r\n to \n for consistent parsing
        buffer = buffer.replace(/\r\n/g, '\n');

        const lastBoundary = buffer.lastIndexOf('\n\n');
        if (lastBoundary === -1) continue;

        const complete = buffer.slice(0, lastBoundary + 2);
        buffer = buffer.slice(lastBoundary + 2);

        const events = parseSSEEvents(complete);

        for (const { event, data } of events) {
          try {
            switch (event) {
              case 'text_delta': {
                const payload = JSON.parse(data) as { text: string };
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: msg.content + payload.text, toolStatus: undefined }
                      : msg
                  )
                );
                break;
              }

              case 'tool_start': {
                const payload = JSON.parse(data) as { tool_name: string; tool_args: Record<string, unknown> };
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, toolStatus: `${getToolDisplayName(payload.tool_name)}...` }
                      : msg
                  )
                );
                break;
              }

              case 'tool_end': {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, toolStatus: undefined }
                      : msg
                  )
                );
                break;
              }

              case 'done': {
                const payload = JSON.parse(data) as { session_id: string };
                if (payload.session_id) {
                  sessionIdRef.current = payload.session_id;
                }
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, isStreaming: false, toolStatus: undefined }
                      : msg
                  )
                );
                break;
              }

              case 'error': {
                const payload = JSON.parse(data) as { message: string };
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? {
                          ...msg,
                          content: msg.content || `Sorry, an error occurred: ${payload.message}`,
                          isStreaming: false,
                          toolStatus: undefined,
                        }
                      : msg
                  )
                );
                break;
              }
            }
          } catch (parseErr) {
            console.warn('Failed to parse SSE event:', data, parseErr);
          }
        }
      }

      // If stream ended without a 'done' event, finalize
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && msg.isStreaming
            ? { ...msg, isStreaming: false, toolStatus: undefined }
            : msg
        )
      );
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, isStreaming: false, toolStatus: undefined }
              : msg
          )
        );
        return;
      }

      console.error('Streaming error:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: msg.content || 'Sorry, I encountered an error connecting to the server. Please try again.',
                isStreaming: false,
                toolStatus: undefined,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  const clearMessages = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
    sessionIdRef.current = null;
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
  };
}
