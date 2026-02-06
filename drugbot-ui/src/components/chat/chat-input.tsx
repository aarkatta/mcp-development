'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  return (
    <motion.div
      className="sticky bottom-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative max-w-3xl mx-auto">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask about medications, side effects, recalls..."
          className="min-h-[52px] max-h-[200px] resize-none pr-14 rounded-2xl border-2 focus:border-primary/50 bg-card shadow-sm transition-all"
          disabled={isLoading}
          rows={1}
        />
        <Button
          size="icon"
          className="absolute right-2 bottom-2 rounded-full h-8 w-8 shadow-sm ai-gradient-bg text-white border-0 hover:opacity-90"
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
      <p className="text-[10px] text-muted-foreground text-center mt-2">
        DrugBot uses FDA data. Always consult a healthcare professional for medical advice.
      </p>
    </motion.div>
  );
}
