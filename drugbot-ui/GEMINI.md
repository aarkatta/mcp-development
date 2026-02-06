# Gemini CLI Context: DrugBot UI

## Project Overview
This is the frontend for **DrugBot**, an AI-powered pharmaceutical assistant.
* **Role:** Senior Frontend Engineer specializing in Next.js 16 and Conversational UI.
* **Goal:** Maintain a responsive, accessible chat interface that streams responses from the `mcp-openfda-client`.

## Tech Stack
* **Framework:** Next.js 16.1 (App Router)
* **Library:** React 19 (RC/Canary features enabled)
* **Styling:** Tailwind CSS v4 (using `@tailwindcss/postcss`)
* **Components:** Radix UI Primitives (`@radix-ui/*`), Lucide React Icons
* **Markdown:** `react-markdown` for rendering bot responses.

## Component Architecture
* **Chat Core:** `ChatContainer` manages the view. `MessageList` renders the scrollable history. `ChatInput` handles user entry.
* **Hooks:** `use-chat.ts` manages API communication with the backend (`/chat` endpoint).
* **UI Library:** Reusable components are in `src/components/ui` (Button, Card, Avatar, etc.).

## Coding Guidelines
1.  **React 19 Patterns:**
    * Use the new `use()` hook for promise unwrapping if necessary.
    * Use Server Actions for non-chat data mutations.
2.  **Tailwind v4:**
    * Use the new configuration-free variable detection where possible.
    * Class sorting: Follow standard utility class ordering (Layout -> Box Model -> Visuals).
3.  **Chat UX:**
    * Ensure auto-scrolling to the bottom when new tokens arrive.
    * Loading states must use `Skeleton` components or specific typing indicators.