export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  toolStatus?: string;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
}
