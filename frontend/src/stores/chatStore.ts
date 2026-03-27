/**
 * Chat state management using Zustand
 */
import { create } from 'zustand';
import type { ChatMessage } from '@/types';

interface ChatStore {
  // State
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;

  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  // Initial state
  messages: [],
  isLoading: false,
  error: null,

  // Add a new message
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: `msg-${Date.now()}-${Math.random()}`,
          timestamp: new Date(),
        },
      ],
    })),

  // Set loading state
  setLoading: (loading) => set({ isLoading: loading }),

  // Set error state
  setError: (error) => set({ error }),

  // Clear all messages
  clearMessages: () => set({ messages: [], error: null }),
}));
