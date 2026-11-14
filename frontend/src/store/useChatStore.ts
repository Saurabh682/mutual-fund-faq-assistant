import { create } from 'zustand';
import {
  createThread,
  deleteThread,
  fetchMetadata,
  fetchSchemeFacts,
  fetchThread,
  fetchThreads,
  sendMessage,
  submitFeedback,
} from '../api/client';
import type { Message, MetaData, SchemeFacts, Thread, ThreadSummary } from '../types/chat';

function getOrCreateClientId(): string {
  const key = 'mf_assistant_client_id';
  let id = localStorage.getItem(key);
  if (!id) {
    id = `client_${Math.random().toString(36).substring(2, 11)}`;
    localStorage.setItem(key, id);
  }
  return id;
}

function getInitialTheme(): 'dark' | 'light' {
  const saved = localStorage.getItem('mf_assistant_theme');
  if (saved === 'dark' || saved === 'light') return saved;
  return 'dark'; // Default to dark per Stitch design archetype
}

interface ChatState {
  clientId: string;
  threads: ThreadSummary[];
  activeThreadId: string | null;
  activeThread: Thread | null;
  meta: MetaData | null;
  schemeFacts: SchemeFacts[];
  /** 'loading' until the first /facts/schemes call settles; 'error' when it failed (the sheet offers a retry) */
  factsState: 'loading' | 'ready' | 'error';
  selectedSchemeId: string;
  isFactSheetOpen: boolean;
  isSidebarOpen: boolean;
  isAboutModalOpen: boolean;
  theme: 'dark' | 'light';
  isLoadingThreads: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  error: string | null;

  // Actions
  init: () => Promise<void>;
  reloadSchemeFacts: () => Promise<void>;
  selectThread: (threadId: string) => Promise<void>;
  startNewThread: (initialQuestion?: string) => Promise<string>;
  removeThread: (threadId: string) => Promise<void>;
  sendUserMessage: (text: string) => Promise<void>;
  setSelectedSchemeId: (schemeId: string) => void;
  toggleFactSheet: (open?: boolean) => void;
  toggleSidebar: () => void;
  closeSidebar: () => void;
  setAboutModalOpen: (open: boolean) => void;
  setTheme: (theme: 'dark' | 'light') => void;
  clearError: () => void;
  submitMessageFeedback: (
    messageId: string,
    rating: 'up' | 'down' | 'reported',
    comment?: string
  ) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  clientId: getOrCreateClientId(),
  threads: [],
  activeThreadId: null,
  activeThread: null,
  meta: null,
  schemeFacts: [],
  factsState: 'loading',
  selectedSchemeId: 'hdfc_midcap_dg',
  isFactSheetOpen: false,
  isSidebarOpen: false,
  isAboutModalOpen: false,
  theme: getInitialTheme(),
  isLoadingThreads: false,
  isLoadingMessages: false,
  isSending: false,
  error: null,

  init: async () => {
    const { clientId, theme } = get();
    // Apply theme to document
    if (typeof document !== 'undefined') {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }

    try {
      set({ isLoadingThreads: true, error: null });
      // A failed fact sheet must show up as a failure (with a retry), not as empty rows
      const factsPromise = fetchSchemeFacts().then(
        (res) => ({ ok: true, schemes: res.schemes || [] }),
        () => ({ ok: false, schemes: [] as SchemeFacts[] })
      );
      const [meta, threads, facts] = await Promise.all([fetchMetadata(), fetchThreads(clientId), factsPromise]);

      const defaultSchemeId =
        meta.schemes && meta.schemes.length > 0 ? meta.schemes[0].id : 'hdfc_midcap_dg';

      set({
        meta,
        threads,
        schemeFacts: facts.schemes,
        factsState: facts.ok ? 'ready' : 'error',
        selectedSchemeId: defaultSchemeId,
        isLoadingThreads: false,
      });

      if (threads.length > 0) {
        await get().selectThread(threads[0].id);
      } else {
        await get().startNewThread();
      }
    } catch (err: unknown) {
      set({
        error: err instanceof Error ? err.message : 'Failed to initialize assistant',
        isLoadingThreads: false,
        factsState: get().factsState === 'loading' ? 'error' : get().factsState,
      });
    }
  },

  reloadSchemeFacts: async () => {
    set({ factsState: 'loading' });
    try {
      const res = await fetchSchemeFacts();
      set({ schemeFacts: res.schemes || [], factsState: 'ready' });
    } catch {
      set({ factsState: 'error' });
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
      const assistantMsg = await sendMessage(activeThreadId, trimmed, clientId);

      // Refresh complete thread state to synchronize message IDs and scheme state
      const updatedThread = await fetchThread(activeThreadId).catch(() => ({
        ...activeThread!,
        messages: [...(activeThread?.messages || []), tempUserMsg, assistantMsg],
      }));
      const updatedThreadsList = await fetchThreads(clientId).catch(() => get().threads);

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

  setSelectedSchemeId: (schemeId: string) => set({ selectedSchemeId: schemeId }),

  toggleFactSheet: (open?: boolean) =>
    set((state) => ({
      isFactSheetOpen: typeof open === 'boolean' ? open : !state.isFactSheetOpen,
    })),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  closeSidebar: () => set({ isSidebarOpen: false }),

  setAboutModalOpen: (open: boolean) => set({ isAboutModalOpen: open }),

  setTheme: (theme: 'dark' | 'light') => {
    localStorage.setItem('mf_assistant_theme', theme);
    if (typeof document !== 'undefined') {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
    set({ theme });
  },

  clearError: () => set({ error: null }),

  submitMessageFeedback: async (
    messageId: string,
    rating: 'up' | 'down' | 'reported',
    comment?: string
  ) => {
    const { activeThread } = get();
    if (!activeThread) return;

    // Optimistically update message
    const updatedMessages = activeThread.messages.map((m) =>
      m.id === messageId ? { ...m, userFeedback: rating } : m
    );

    set({
      activeThread: {
        ...activeThread,
        messages: updatedMessages,
      },
    });

    await submitFeedback({
      message_id: messageId,
      rating,
      comment,
    });
  },
}));
