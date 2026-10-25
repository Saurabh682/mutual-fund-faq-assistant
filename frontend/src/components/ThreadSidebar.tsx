import React, { useState } from 'react';
import {
  Moon,
  Plus,
  Search,
  Settings,
  Trash2,
  X,
} from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const ThreadSidebar: React.FC = () => {
  const [filterText, setFilterText] = useState('');
  const {
    threads,
    activeThreadId,
    selectThread,
    startNewThread,
    removeThread,
    isSidebarOpen,
    closeSidebar,
    clientId,
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

  const filteredThreads = threads.filter((t) =>
    t.title.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {isSidebarOpen && (
        <div
          onClick={closeSidebar}
          className="fixed inset-0 bg-[#12161A]/80 backdrop-blur-xs z-30 md:hidden"
        />
      )}

      {/* Sidebar container (Fixed 280px width) */}
      <aside
        className={`w-[280px] shrink-0 bg-[#151A20] border-r border-[#28323E] flex flex-col justify-between z-40 transition-transform duration-200 ease-in-out md:translate-x-0 ${
          isSidebarOpen ? 'fixed top-0 bottom-0 left-0 translate-x-0' : 'fixed -translate-x-full md:relative md:flex'
        }`}
      >
        {/* Upper Section */}
        <div className="p-4 flex flex-col gap-4 flex-1 overflow-y-auto">
          {/* Brand Header */}
          <div className="flex items-center justify-between pb-2 border-b border-[#28323E]/60">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#00D09C] to-[#00f5b8] p-[1.5px] flex items-center justify-center shadow-lg shadow-[#00D09C]/15">
                <div className="w-full h-full bg-[#12161A] rounded-[10px] flex items-center justify-center font-bold text-sm text-[#00D09C]">
                  G
                </div>
              </div>
              <div>
                <div className="flex items-center gap-1.5 leading-none">
                  <span className="font-bold text-sm tracking-tight text-white">groww</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#00D09C]"></span>
                  <span className="text-xs text-slate-300 font-semibold tracking-wide">MF INSIGHTS</span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">HDFC Scheme Facts v2.4</span>
              </div>
            </div>
            <button
              onClick={closeSidebar}
              title="Close sidebar"
              className="md:hidden p-1 rounded text-slate-500 hover:text-slate-300 hover:bg-[#1A2027] transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* "New Fact Query" primary button */}
          <button
            onClick={handleNew}
            className="w-full py-2.5 px-3 rounded-xl border border-[#00D09C] bg-[#00D09C]/5 hover:bg-[#00D09C]/15 text-[#00D09C] font-semibold text-xs flex items-center justify-between transition-all group shadow-xs hover:shadow-[0_0_15px_rgba(0,208,156,0.2)] cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-md bg-[#00D09C] text-[#12161A] flex items-center justify-center group-hover:scale-105 transition-transform">
                <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
              </div>
              <span>New Fact Query</span>
            </div>
            <span className="px-1.5 py-0.5 rounded bg-[#202832] border border-[#28323E] text-[10px] text-slate-400 font-mono tracking-tighter">
              Ctrl+K
            </span>
          </button>

          {/* Search Filter Bar */}
          <div className="relative">
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Filter questions..."
              className="w-full bg-[#1A2027] border border-[#28323E] rounded-lg px-2.5 py-1.5 pl-8 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#00D09C]/60 focus:ring-1 focus:ring-[#00D09C]/40 transition"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
          </div>

          {/* Conversation History List */}
          <div className="flex flex-col gap-4 mt-1">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-2 mb-1.5 flex items-center justify-between">
                <span>Conversations</span>
                <span className="font-mono text-slate-600">({filteredThreads.length})</span>
              </div>

              {filteredThreads.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-500 font-mono">
                  No conversations found
                </div>
              ) : (
                filteredThreads.map((t) => {
                  const isActive = t.id === activeThreadId;
                  return (
                    <div
                      key={t.id}
                      onClick={() => handleSelect(t.id)}
                      className={`relative group rounded-lg p-2.5 flex items-center justify-between cursor-pointer transition overflow-hidden mb-1 ${
                        isActive
                          ? 'bg-[#1A2027] border border-[#28323E] shadow-xs'
                          : 'hover:bg-[#1A2027]/70 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00D09C]" />}
                      <div className="flex flex-col gap-0.5 pl-1.5 pr-2 truncate">
                        <span className={`text-xs truncate ${isActive ? 'font-semibold text-white' : 'font-medium'}`}>
                          {t.title}
                        </span>
                        <span className="text-[10px] text-slate-400 flex items-center gap-1.5">
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          {t.last_scheme_id ? t.last_scheme_id.replace('_dg', '').replace('hdfc_', '').toUpperCase() : 'HDFC MF'} • Facts verified
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0 ml-2">
                        <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-[#202832] text-slate-300 border border-[#28323E] leading-none shrink-0 num-tabular">
                          {t.message_count || 1} msgs
                        </span>
                        <button
                          onClick={(e) => handleDelete(e, t.id)}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:text-red-400 text-slate-500 transition cursor-pointer"
                          title="Delete conversation"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 bg-[#12161A] border-t border-[#28323E] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#1A2027] border border-[#28323E] flex items-center justify-center text-[10px] font-mono text-slate-300">
              ID
            </div>
            <div className="flex flex-col">
              <span className="text-[11px] font-mono text-slate-300 leading-tight truncate max-w-[120px]">
                {clientId}
              </span>
              <span className="text-[9px] text-[#00D09C] flex items-center gap-1 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00D09C]"></span> Connected
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-[#1A2027] transition"
              title="Dark mode active"
            >
              <Moon className="w-3.5 h-3.5" />
            </button>
            <button
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-[#1A2027] transition"
              title="Settings"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
