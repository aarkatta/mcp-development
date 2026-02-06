'use client';

import { useChat } from '@/hooks/use-chat';
import { MessageList } from './message-list';
import { ChatInput } from './chat-input';
import { Button } from '@/components/ui/button';
import { Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';

export function ChatContainer() {
  const { messages, isLoading, sendMessage, clearMessages } = useChat();

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] pb-12 md:pb-0">
      {/* Chat status bar */}
      {messages.length > 0 && (
        <motion.div
          className="flex items-center justify-between border-b px-4 py-2 bg-card"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-muted-foreground">
              {isLoading ? (
                <span className="ai-gradient-text font-medium">DrugBot is thinking...</span>
              ) : (
                'DrugBot is online'
              )}
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-muted-foreground hover:text-destructive"
            onClick={clearMessages}
          >
            <Trash2 className="h-3 w-3 mr-1" />
            Clear chat
          </Button>
        </motion.div>
      )}

      <MessageList messages={messages} isLoading={isLoading} onSendMessage={sendMessage} />

      <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  );
}
