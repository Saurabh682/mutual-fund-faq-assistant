import React, { useEffect, useState } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { CompareDrawer } from './components/CompareDrawer';
import { Composer } from './components/Composer';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { Header } from './components/Header';
import { MessageFeed } from './components/MessageFeed';
import { ThreadSidebar } from './components/ThreadSidebar';
import { useChatStore } from './store/useChatStore';

export const App: React.FC = () => {
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const { init, error, clearError, sendUserMessage } = useChatStore();

  useEffect(() => {
    init();
  }, [init]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#12161A] text-white selection:bg-[#00D09C]/20 selection:text-[#00D09C]">
      {/* 1. Mandatory Top Compliance Header (44px) */}
      <DisclaimerBanner />

      {/* 2. Main App Container (Sidebar + Content Workspace) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar (280px Fixed Width) */}
        <ThreadSidebar />

        {/* Main Chat Workspace */}
        <main className="flex-1 flex flex-col bg-[#12161A] overflow-hidden relative">
          {/* Top App Bar */}
          <Header onOpenCompare={() => setIsCompareOpen(true)} />

          {/* Error Toast */}
          {error && (
            <div className="bg-red-950/80 border-b border-red-800 px-4 py-2 text-xs text-red-200 flex items-center justify-between z-20">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{error}</span>
              </div>
              <button
                onClick={clearError}
                className="p-1 hover:bg-red-900 rounded cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Feed Container */}
          <MessageFeed />

          {/* Bottom Composer */}
          <Composer />

          {/* Comparison Drawer Panel */}
          <CompareDrawer
            isOpen={isCompareOpen}
            onClose={() => setIsCompareOpen(false)}
            onInsertComparison={(text) => sendUserMessage(text)}
          />
        </main>
      </div>
    </div>
  );
};

export default App;
