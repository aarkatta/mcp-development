# ChatGPT-Style Chatbot UI with MCP Client

## Project Overview

A proof-of-concept chatbot interface built with Next.js and ShadCN UI that connects to a Model Context Protocol (MCP) client. The UI design mimics ChatGPT's clean, conversational interface.

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **UI Library**: ShadCN UI (Radix primitives + Tailwind CSS)
- **Styling**: Tailwind CSS
- **State Management**: React hooks / Zustand (optional)
- **Backend Integration**: MCP Client SDK

---

## ShadCN Components for ChatGPT-Like UI

### Core Chat Components

| Component | Purpose | Installation |
|-----------|---------|--------------|
| **ScrollArea** | Scrollable chat message container | `npx shadcn@latest add scroll-area` |
| **Avatar** | User and AI profile icons | `npx shadcn@latest add avatar` |
| **Button** | Send, regenerate, copy, new chat | `npx shadcn@latest add button` |
| **Textarea** | Multi-line message input | `npx shadcn@latest add textarea` |
| **Card** | Message bubble containers | `npx shadcn@latest add card` |

### Sidebar & Navigation

| Component | Purpose | Installation |
|-----------|---------|--------------|
| **Sheet** | Mobile sidebar (chat history) | `npx shadcn@latest add sheet` |
| **Sidebar** | Desktop conversation list | `npx shadcn@latest add sidebar` |
| **Separator** | Visual dividers | `npx shadcn@latest add separator` |
| **Tooltip** | Action button hints | `npx shadcn@latest add tooltip` |

### Interaction & Feedback

| Component | Purpose | Installation |
|-----------|---------|--------------|
| **Skeleton** | Loading states for messages | `npx shadcn@latest add skeleton` |
| **DropdownMenu** | Model selector, options menu | `npx shadcn@latest add dropdown-menu` |
| **Dialog** | Settings, confirmations | `npx shadcn@latest add dialog` |
| **Badge** | Model tags, status indicators | `npx shadcn@latest add badge` |
| **Toggle** | Theme switch, feature toggles | `npx shadcn@latest add toggle` |

### Quick Install All

```bash
npx shadcn@latest add scroll-area avatar button textarea card sheet sidebar separator tooltip skeleton dropdown-menu dialog badge toggle
```

---

## Project Structure

```
src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── api/
│       └── chat/
│           └── route.ts          # MCP client API endpoint
├── components/
│   ├── chat/
│   │   ├── chat-container.tsx    # Main chat wrapper
│   │   ├── message-list.tsx      # Scrollable messages
│   │   ├── message-bubble.tsx    # Individual message
│   │   ├── chat-input.tsx        # Input area with send button
│   │   ├── typing-indicator.tsx  # AI typing animation
│   │   └── code-block.tsx        # Syntax highlighted code
│   ├── sidebar/
│   │   ├── chat-sidebar.tsx      # Conversation history
│   │   ├── chat-item.tsx         # Single conversation entry
│   │   └── new-chat-button.tsx
│   ├── layout/
│   │   ├── header.tsx            # Top navigation
│   │   └── model-selector.tsx    # Model dropdown
│   └── ui/                       # ShadCN components
├── hooks/
│   ├── use-chat.ts               # Chat state management
│   ├── use-mcp-client.ts         # MCP client hook
│   └── use-scroll-anchor.ts      # Auto-scroll to bottom
├── lib/
│   ├── mcp-client.ts             # MCP client configuration
│   ├── utils.ts                  # ShadCN utilities
│   └── types.ts                  # TypeScript interfaces
└── styles/
    └── globals.css               # Tailwind + custom styles
```

---

## Key UI Patterns

### 1. Message Bubble Layout

```tsx
// ChatGPT-style: alternating full-width rows
<div className="flex flex-col gap-4">
  {/* User message - right aligned icon */}
  <div className="flex gap-3 justify-end">
    <div className="max-w-[80%] bg-primary text-primary-foreground rounded-2xl px-4 py-2">
      {userMessage}
    </div>
    <Avatar />
  </div>
  
  {/* AI message - left aligned icon */}
  <div className="flex gap-3">
    <Avatar />
    <div className="max-w-[80%] bg-muted rounded-2xl px-4 py-2">
      {aiMessage}
    </div>
  </div>
</div>
```

### 2. Input Area (Sticky Bottom)

```tsx
<div className="sticky bottom-0 border-t bg-background p-4">
  <div className="relative max-w-3xl mx-auto">
    <Textarea 
      placeholder="Message ChatBot..."
      className="min-h-[52px] resize-none pr-12 rounded-2xl"
    />
    <Button 
      size="icon" 
      className="absolute right-2 bottom-2 rounded-full"
    >
      <Send className="h-4 w-4" />
    </Button>
  </div>
</div>
```

### 3. Sidebar Toggle Pattern

```tsx
// Desktop: persistent sidebar
// Mobile: Sheet component overlay
<Sheet>
  <SheetTrigger asChild>
    <Button variant="ghost" size="icon" className="md:hidden">
      <Menu />
    </Button>
  </SheetTrigger>
  <SheetContent side="left">
    <ChatSidebar />
  </SheetContent>
</Sheet>
```

---

## MCP Client Integration

### Basic Hook Pattern

```typescript
// hooks/use-mcp-client.ts
import { useState, useCallback } from 'react';

interface MCPMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function useMCPClient() {
  const [messages, setMessages] = useState<MCPMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);
    setMessages(prev => [...prev, { role: 'user', content }]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          messages: [...messages, { role: 'user', content }]
        }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('MCP Client Error:', error);
    } finally {
      setIsLoading(false);
    }
  }, [messages]);

  return { messages, isLoading, sendMessage };
}
```

### API Route (App Router)

```typescript
// app/api/chat/route.ts
import { NextRequest, NextResponse } from 'next/server';
// Import your MCP client SDK here

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  
  // TODO: Initialize and call your MCP client
  // const mcpClient = new MCPClient({ serverUrl: process.env.MCP_SERVER_URL });
  // const response = await mcpClient.chat(messages);
  
  return NextResponse.json({ 
    response: 'MCP response placeholder' 
  });
}
```

---

## Design Guidelines

### Color Scheme (ChatGPT-inspired)

```css
/* globals.css - Dark theme variables */
:root {
  --background: 0 0% 7%;           /* #121212 - Main background */
  --foreground: 0 0% 95%;          /* #F2F2F2 - Text */
  --muted: 0 0% 15%;               /* #262626 - AI message bg */
  --muted-foreground: 0 0% 65%;    /* #A6A6A6 - Secondary text */
  --primary: 142 70% 45%;          /* Green accent (like ChatGPT) */
  --card: 0 0% 10%;                /* #1A1A1A - Sidebar */
  --border: 0 0% 20%;              /* #333333 - Borders */
  --input: 0 0% 12%;               /* Input background */
}
```

### Typography

```css
/* Clean, readable font stack */
body {
  font-family: 'Söhne', 'Helvetica Neue', Arial, sans-serif;
  /* Or use: ui-sans-serif, system-ui, sans-serif */
}

/* Code blocks */
pre, code {
  font-family: 'Söhne Mono', 'Menlo', 'Monaco', monospace;
}
```

### Key Visual Elements

1. **Rounded corners**: Use `rounded-2xl` for messages, `rounded-full` for buttons
2. **Subtle shadows**: `shadow-sm` on cards, no harsh shadows
3. **Generous padding**: `p-4` minimum on containers
4. **Max-width constraint**: Center content with `max-w-3xl mx-auto`
5. **Smooth transitions**: `transition-all duration-200` on interactive elements

---

## Getting Started

```bash
# 1. Create Next.js project
npx create-next-app@latest drugbot-ui --typescript --tailwind --eslint --app

# 2. Initialize ShadCN
cd drugbot-ui
npx shadcn@latest init

# 3. Install required components
npx shadcn@latest add scroll-area avatar button textarea card sheet sidebar separator tooltip skeleton dropdown-menu dialog badge toggle

# 4. Install additional dependencies
npm install lucide-react  # Icons (included with ShadCN)

# 5. Start development
npm run dev
```

---

## Reference Links

- [ShadCN UI Docs](https://ui.shadcn.com/)
- [ShadCN Sidebar](https://ui.shadcn.com/docs/components/sidebar)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev/icons/)
- [MCP Specification](https://modelcontextprotocol.io/)

---

## Notes for POC

- Focus on UI/UX first, mock API responses initially
- Use streaming responses later for better UX (`ReadableStream`)
- Consider `react-markdown` + `react-syntax-highlighter` for message rendering
- Keep state simple with `useState` before adding Zustand/Context
