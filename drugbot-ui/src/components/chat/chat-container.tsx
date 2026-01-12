'use client';

import { useChat } from '@/hooks/use-chat';
import { MessageList } from './message-list';
import { ChatInput } from './chat-input';

export function ChatContainer() {
  const { messages, isLoading, sendMessage } = useChat();

  return (
    <div className="flex flex-col h-screen bg-background">
      <header className="border-b px-4 py-3">
        <h1 className="text-lg font-semibold text-center">DrugBot</h1>
      </header>

      <MessageList messages={messages} isLoading={isLoading} />

      <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  );
}
