import { create } from 'zustand';
import {
  createThread,
  deleteThread,
  fetchMetadata,
  fetchThread,
  fetchThreads,
  sendMessage,
} from '../api/client';
import type { Message, MetaData, Thread, ThreadSummary } from '../types/chat';

function getOrCreateClientId(): string {
  const key = 'mf_assistant_client_id';
  let id = localStorage.getItem(key);
  if (!id) {
    id = `client_${Math.random().toString(36).substring(2, 11)}`;
    localStorage.setItem(key, id);
  }
  return id;
}

interface ChatState {
  clientId: string;
  threads: ThreadSummary[];
  activeThreadId: string | null;
  activeThread: Thread | null;
  meta: MetaData | null;
  isLoadingThreads: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  isSidebarOpen: boolean;
  error: string | null;

  // Actions
  init: () => Promise<void>;
  selectThread: (threadId: string) => Promise<void>;
  startNewThread: (initialQuestion?: string) => Promise<string>;
  removeThread: (threadId: string) => Promise<void>;
  sendUserMessage: (text: string) => Promise<void>;
  toggleSidebar: () => void;
  closeSidebar: () => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  clientId: getOrCreateClientId(),
  threads: [],
  activeThreadId: null,
  activeThread: null,
  meta: null,
  isLoadingThreads: false,
  isLoadingMessages: false,
  isSending: false,
  isSidebarOpen: false,
  error: null,

  init: async () => {
    const { clientId } = get();
    try {
      set({ isLoadingThreads: true, error: null });
      const [meta, threads] = await Promise.all([
        fetchMetadata(),
        fetchThreads(clientId),
      ]);
      set({ meta, threads, isLoadingThreads: false });

      if (threads.length > 0) {
        await get().selectThread(threads[0].id);
      } else {
        await get().startNewThread();
      }
    } catch (err: unknown) {
      set({
        error: err instanceof Error ? err.message : 'Failed to initialize assistant',
        isLoadingThreads: false,
      });
    }
  },

  selectThread: async (threadId: string) => {
    try {
      set({ activeThreadId: threadId, isLoadingMessages: true, error: null });
      const thread = await fetchThread(threadId);
      set({ activeThread: thread, isLoadingMessages: false });
    } catch (err: unknown) {
      set({
        error: err instanceof Error ? err.message : `Failed to load thread ${threadId}`,
        isLoadingMessages: false,
      });
    }
  },

  startNewThread: async (initialQuestion?: string): Promise<string> => {
    const { clientId } = get();
    try {
      set({ isSending: true, error: null });
      const newThread = await createThread(
        clientId,
        initialQuestion ? initialQuestion.substring(0, 35) : 'New Conversation'
      );

      set((state) => ({
        threads: [
          {
            id: newThread.id,
            client_id: newThread.client_id,
            title: newThread.title,
            last_scheme_id: newThread.last_scheme_id,
            created_at: newThread.created_at,
            updated_at: newThread.updated_at,
            message_count: 0,
          },
          ...state.threads,
        ],
        activeThreadId: newThread.id,
        activeThread: newThread,
        isSending: false,
      }));

      if (initialQuestion) {
        await get().sendUserMessage(initialQuestion);
      }

      return newThread.id;
    } catch (err: unknown) {
      set({
        error: err instanceof Error ? err.message : 'Failed to create new thread',
        isSending: false,
      });
      return '';
    }
  },

  removeThread: async (threadId: string) => {
    try {
      await deleteThread(threadId);
      const remainingThreads = get().threads.filter((t) => t.id !== threadId);
      set({ threads: remainingThreads });

      if (get().activeThreadId === threadId) {
        if (remainingThreads.length > 0) {
          await get().selectThread(remainingThreads[0].id);
        } else {
          await get().startNewThread();
        }
      }
    } catch (err: unknown) {
      set({
        error: err instanceof Error ? err.message : `Failed to delete thread ${threadId}`,
      });
    }
  },

  sendUserMessage: async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    let { activeThreadId } = get();
    const { clientId, activeThread } = get();

    if (!activeThreadId) {
      activeThreadId = await get().startNewThread();
    }

    // Optimistically append user message
    const tempUserMsg: Message = {
      id: `temp_${Date.now()}`,
      role: 'user',
      type: 'user_query',
      text: trimmed,
      timestamp: new Date().toISOString(),
    };

    set({
      isSending: true,
      error: null,
      activeThread: activeThread
        ? {
            ...activeThread,
            messages: [...activeThread.messages, tempUserMsg],
          }
        : null,
    });

    try {
      await sendMessage(activeThreadId, trimmed, clientId);

      // Refresh complete thread state to synchronize message IDs and scheme state
      const updatedThread = await fetchThread(activeThreadId);
      const updatedThreadsList = await fetchThreads(clientId);

      set({
        activeThread: updatedThread,
        threads: updatedThreadsList,
        isSending: false,
      });
    } catch (err: unknown) {
      set({
        error: err instanceof Error ? err.message : 'Failed to send message',
        isSending: false,
      });
    }
  },

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  closeSidebar: () => set({ isSidebarOpen: false }),
  clearError: () => set({ error: null }),
}));
