'use client';

import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { MessageBubble } from './message-bubble';
import { Message } from '@/lib/types';
import { Bot } from 'lucide-react';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

function TypingIndicator() {
  return (
    <div className="flex gap-3 w-full justify-start">
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className="bg-primary text-primary-foreground">
          <Bot className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="bg-muted rounded-2xl px-4 py-3">
        <div className="flex gap-1">
          <Skeleton className="h-2 w-2 rounded-full animate-pulse" />
          <Skeleton className="h-2 w-2 rounded-full animate-pulse delay-150" />
          <Skeleton className="h-2 w-2 rounded-full animate-pulse delay-300" />
        </div>
      </div>
    </div>
  );
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <ScrollArea className="flex-1 p-4" ref={scrollRef}>
      <div className="flex flex-col gap-4 max-w-3xl mx-auto">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full py-20 text-center">
            <Bot className="h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">Welcome to DrugBot</h2>
            <p className="text-muted-foreground max-w-md">
              Ask me anything about medications, drug interactions, side effects, or dosage information.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && <TypingIndicator />}
      </div>
    </ScrollArea>
  );
}
