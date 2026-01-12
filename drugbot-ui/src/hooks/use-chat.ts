'use client';

import { useState, useCallback, useRef } from 'react';
import { Message } from '@/lib/types';

const MCP_CLIENT_URL = 'http://localhost:8080/chat';

function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const payload = {
        message: content.trim(),
        session_id: sessionIdRef.current,
      };

      console.log('Sending request to:', MCP_CLIENT_URL);
      console.log('Request payload:', payload);

      const response = await fetch(MCP_CLIENT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();
      console.log('=== MCP Server Response ===', data);

      // Update session ID for next turn
      if (data.session_id) {
        sessionIdRef.current = data.session_id;
        console.log('Session ID updated:', data.session_id);
      }

      const messageContent = data.output || data.response;
      console.log('Final messageContent:', messageContent);

      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: messageContent,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('MCP Client Error:', error);

      const errorMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: 'Sorry, I encountered an error connecting to the server. Please make sure the MCP client is running on localhost:8080.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = null; // Reset session on clear
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
  };
}
