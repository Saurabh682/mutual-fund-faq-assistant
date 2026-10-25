import React, { useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Composer } from './components/Composer';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { Header } from './components/Header';
import { MessageFeed } from './components/MessageFeed';
import { ThreadSidebar } from './components/ThreadSidebar';
import { useChatStore } from './store/useChatStore';

export const App: React.FC = () => {
  const { init, error, clearError } = useChatStore();

  useEffect(() => {
    init();
  }, [init]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#F8F9FA] dark:bg-[#0F1419] text-[#1A1E24] dark:text-[#F3F4F6]">
      {/* 1. Persistent Regulatory Disclaimer */}
      <DisclaimerBanner />

      {/* 2. Top Header */}
      <Header />

      {/* Error Toast if present */}
      {error && (
        <div className="bg-red-50 dark:bg-red-950/70 border-b border-red-200 dark:border-red-900 px-4 py-2 text-xs text-red-700 dark:text-red-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
          <button
            onClick={clearError}
            className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 3. Main Workspace Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <ThreadSidebar />

        {/* Chat Feed & Input */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative">
          <MessageFeed />
          <Composer />
        </main>
      </div>
    </div>
  );
};

export default App;
