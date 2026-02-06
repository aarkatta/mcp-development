'use client';

import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { MessageBubble } from './message-bubble';
import { Message } from '@/lib/types';
import { Pill, Sparkles, Shield, Search } from 'lucide-react';
import { motion } from 'framer-motion';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
}

function TypingIndicator() {
  return (
    <motion.div
      className="flex gap-3 w-full justify-start"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className="ai-gradient-bg text-white">
          <Pill className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="bg-muted rounded-2xl px-4 py-3">
        <div className="flex gap-1.5">
          <Skeleton className="h-2 w-2 rounded-full animate-pulse" />
          <Skeleton className="h-2 w-2 rounded-full animate-pulse [animation-delay:150ms]" />
          <Skeleton className="h-2 w-2 rounded-full animate-pulse [animation-delay:300ms]" />
        </div>
      </div>
    </motion.div>
  );
}

const suggestedQueries = [
  { icon: Search, text: "What are the side effects of Lisinopril?", iconClass: "ai-icon-purple" },
  { icon: Shield, text: "Show me recent drug recalls", iconClass: "ai-icon-blue" },
  { icon: Sparkles, text: "Tell me about drug shortages", iconClass: "ai-icon-teal" },
];

export function MessageList({ messages, isLoading, onSendMessage }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <ScrollArea className="flex-1 p-4" ref={scrollRef}>
      <div className="flex flex-col gap-4 max-w-6xl mx-auto px-2 md:px-6">
        {messages.length === 0 && !isLoading && (
          <motion.div
            className="flex flex-col items-center justify-center h-full py-16 text-center"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <motion.div
              className="flex h-16 w-16 items-center justify-center rounded-2xl ai-gradient-bg mb-6"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            >
              <Pill className="h-8 w-8 text-white" />
            </motion.div>
            <motion.h2
              className="text-2xl font-bold mb-2 ai-gradient-text"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              Welcome to DrugBot
            </motion.h2>
            <motion.p
              className="text-muted-foreground max-w-md mb-8"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              Your AI-powered pharmaceutical assistant. Ask about medications, drug interactions, side effects, recalls, and shortages.
            </motion.p>

            <motion.div
              className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-2xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              {suggestedQueries.map((query, index) => {
                const Icon = query.icon;
                return (
                  <motion.button
                    key={index}
                    className="flex flex-col items-center gap-2 rounded-xl border bg-card p-4 text-sm text-card-foreground hover:bg-accent hover:shadow-md transition-all cursor-pointer ai-gradient-border"
                    whileHover={{ y: -2 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => onSendMessage(query.text)}
                  >
                    <Icon className={`h-5 w-5 ${query.iconClass}`} />
                    <span className="text-xs text-muted-foreground text-center leading-tight">
                      {query.text}
                    </span>
                  </motion.button>
                );
              })}
            </motion.div>
          </motion.div>
        )}

        {messages.map((message, index) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index === messages.length - 1 ? 0.1 : 0 }}
          >
            <MessageBubble message={message} />
          </motion.div>
        ))}

        {isLoading && <TypingIndicator />}
      </div>
    </ScrollArea>
  );
}
