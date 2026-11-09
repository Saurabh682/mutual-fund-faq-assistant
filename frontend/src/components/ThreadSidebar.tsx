import React from 'react';
import {
  MessageSquare,
  Moon,
  Plus,
  Sun,
  Trash2,
  User,
  X,
} from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const ThreadSidebar: React.FC = () => {
  const {
    threads,
    activeThreadId,
    selectThread,
    startNewThread,
    removeThread,
    isSidebarOpen,
    closeSidebar,
    theme,
    setTheme,
    isSending,
  } = useChatStore();

  const handleNewChat = () => {
    if (isSending) return;
    startNewThread();
    closeSidebar();
  };

  const handleSelectThread = (threadId: string) => {
    selectThread(threadId);
    closeSidebar();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          onClick={closeSidebar}
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-xs transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Aside */}
      <aside
        className={`fixed lg:static top-0 left-0 h-full w-[260px] flex flex-col justify-between z-50 transition-transform duration-200 ease-in-out border-r shadow-sm shrink-0 bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1f2824] ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col min-h-0 flex-1">
          {/* Top Brand Header */}
          <div className="h-16 px-4 flex items-center justify-between border-b border-[#F1F5F9] dark:border-[#1f2824] shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border bg-emerald-50 border-emerald-200 text-[#059669] dark:bg-[#10b981]/15 dark:border-[#10b981]/40 dark:text-[#10b981]">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <rect height="12" rx="2" width="12" x="3" y="3" />
                  <path d="M9 15v4a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-4" />
                </svg>
              </div>
              <span className="text-[18px] font-bold text-[#0F172A] dark:text-[#dde4df] tracking-tight">
                FundFacts
              </span>
            </div>
            {/* Mobile close button */}
            <button
              onClick={closeSidebar}
              className="lg:hidden w-11 h-11 flex items-center justify-center text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#dde4df] rounded-lg cursor-pointer"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-3 shrink-0">
            <button
              onClick={handleNewChat}
              disabled={isSending}
              className="w-full min-h-[44px] flex items-center justify-center gap-2 py-2 px-4 rounded-xl font-semibold text-[14px] shadow-sm transition-colors cursor-pointer bg-[#059669] text-white hover:bg-[#047857] dark:bg-[#10b981] dark:text-[#00422b] dark:hover:bg-[#4edea3] disabled:opacity-50"
              type="button"
            >
              <Plus className="w-4 h-4" />
              <span>New chat</span>
            </button>
          </div>

          {/* Conversations Section */}
          <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
            <div className="px-2 pb-1.5 text-[13px] font-semibold uppercase tracking-wider text-[#64748B] dark:text-[#94a3b8]">
              Conversations
            </div>
            {threads.length === 0 ? (
              <div className="px-2 py-4 text-[13px] text-[#64748B] dark:text-[#94a3b8] text-center">
                No conversations yet
              </div>
            ) : (
              <nav className="flex flex-col gap-1" aria-label="Conversation history">
                {threads.map((t) => {
                  const isActive = t.id === activeThreadId;
                  return (
                    <div
                      key={t.id}
                      className={`group relative flex items-center justify-between rounded-xl transition-colors min-h-[44px] px-2.5 py-1.5 ${
                        isActive
                          ? 'bg-emerald-50 text-[#059669] border border-emerald-100 font-semibold dark:bg-[#16201b] dark:text-[#10b981] dark:border-[#2f3633]'
                          : 'text-[#475569] hover:bg-[#F1F5F9] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:bg-[#16201b] dark:hover:text-[#dde4df]'
                      }`}
                    >
                      <button
                        onClick={() => handleSelectThread(t.id)}
                        className="flex items-center gap-2 flex-1 text-left min-w-0 min-h-[44px] cursor-pointer"
                        title={t.title}
                      >
                        <MessageSquare
                          className={`w-4 h-4 shrink-0 ${
                            isActive
                              ? 'text-[#059669] dark:text-[#10b981]'
                              : 'text-[#64748B] dark:text-[#86948a]'
                          }`}
                        />
                        <span className="truncate text-[13px] leading-snug">
                          {t.title || 'New Conversation'}
                        </span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeThread(t.id);
                        }}
                        aria-label={`Delete conversation ${t.title}`}
                        className="opacity-0 group-hover:opacity-100 focus:opacity-100 w-8 h-8 flex items-center justify-center rounded text-[#64748B] hover:text-red-500 transition-opacity cursor-pointer shrink-0"
                        title="Delete conversation"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </nav>
            )}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3.5 border-t border-[#E2E8F0] bg-[#F8FAFC] dark:border-[#1f2824] dark:bg-[#09100d] shrink-0 space-y-2.5">
          {/* Guest User profile */}
          <div className="flex items-center gap-2.5 px-1 py-1">
            <div className="w-8 h-8 rounded-full flex items-center justify-center border shadow-xs bg-white border-[#E2E8F0] text-[#475569] dark:bg-[#242c28] dark:border-[#2f3633] dark:text-[#dde4df]">
              <User className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-[13px] font-semibold text-[#0F172A] dark:text-[#dde4df]">
                Guest User
              </span>
              <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8]">
                Local session
              </span>
            </div>
          </div>

          {/* Theme Selector */}
          <div className="flex items-center justify-between px-2.5 py-1.5 rounded-xl border bg-white border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
            <span className="text-[13px] font-medium text-[#64748B] dark:text-[#94a3b8]">
              Theme
            </span>
            <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#F1F5F9] dark:bg-[#131a17]">
              <button
                onClick={() => setTheme('dark')}
                className={`min-h-[32px] px-2.5 py-1 rounded-md text-[13px] font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                  theme === 'dark'
                    ? 'bg-[#2f3633] text-[#dde4df] shadow-xs'
                    : 'text-[#94a3b8] hover:text-[#dde4df]'
                }`}
                type="button"
                aria-pressed={theme === 'dark'}
              >
                <Moon className="w-3.5 h-3.5" />
                <span>Dark</span>
              </button>
              <button
                onClick={() => setTheme('light')}
                className={`min-h-[32px] px-2.5 py-1 rounded-md text-[13px] font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                  theme === 'light'
                    ? 'bg-white text-[#0F172A] shadow-xs'
                    : 'text-[#64748B] hover:text-[#0F172A]'
                }`}
                type="button"
                aria-pressed={theme === 'light'}
              >
                <Sun className="w-3.5 h-3.5 text-amber-500" />
                <span>Light</span>
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
