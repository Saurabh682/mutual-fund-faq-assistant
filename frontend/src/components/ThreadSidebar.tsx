import React from 'react';
import { MessageSquare, Plus, Trash2, X } from 'lucide-react';
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
  } = useChatStore();

  const handleSelect = async (id: string) => {
    await selectThread(id);
    closeSidebar();
  };

  const handleNew = async () => {
    await startNewThread();
    closeSidebar();
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      await removeThread(id);
    }
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white dark:bg-[#12161A] border-r border-gray-200 dark:border-gray-800 w-72 sm:w-80 select-none">
      {/* Top action */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between gap-2">
        <button
          onClick={handleNew}
          className="flex-1 flex items-center justify-center gap-2 bg-[#00b386] hover:bg-[#00d09c] text-white font-medium text-sm py-2.5 px-4 rounded-xl transition shadow-sm shadow-[#00b386]/20 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>

        <button
          onClick={closeSidebar}
          className="md:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-white rounded-lg"
          aria-label="Close Sidebar"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Threads list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 px-3 py-1.5">
          Conversations ({threads.length})
        </div>

        {threads.length === 0 ? (
          <div className="text-center py-8 text-xs text-gray-400">
            No conversations yet. Start one above!
          </div>
        ) : (
          threads.map((t) => {
            const isActive = t.id === activeThreadId;
            return (
              <div
                key={t.id}
                onClick={() => handleSelect(t.id)}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer text-sm transition ${
                  isActive
                    ? 'bg-[#00b386]/10 text-[#00b386] font-semibold border border-[#00b386]/30'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-2">
                  <MessageSquare
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? 'text-[#00b386]' : 'text-gray-400 dark:text-gray-500'
                    }`}
                  />
                  <div className="truncate">
                    <p className="truncate text-xs md:text-sm">{t.title}</p>
                    <p className="text-[10px] text-gray-400 dark:text-gray-500">
                      {new Date(t.updated_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>

                <button
                  onClick={(e) => handleDelete(e, t.id)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/40 transition shrink-0"
                  aria-label={`Delete ${t.title}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer info */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-800 text-[11px] text-gray-400 text-center">
        <span>Strictly 5 HDFC Groww Schemes</span>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop permanent sidebar */}
      <aside className="hidden md:block h-full shrink-0">{sidebarContent}</aside>

      {/* Mobile drawer with backdrop */}
      {isSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
            onClick={closeSidebar}
            aria-hidden="true"
          />
          <div className="relative z-50 h-full">{sidebarContent}</div>
        </div>
      )}
    </>
  );
};
