import React, { useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { AboutModal } from './components/AboutModal';
import { Composer } from './components/Composer';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { FactSheetContent, FactSheetDrawer } from './components/FactSheetDrawer';
import { Footer } from './components/Footer';
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
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#F8FAFC] dark:bg-[#0e1512] text-[#0F172A] dark:text-[#dde4df] transition-colors">
      {/* 1. Top Compliance Disclaimer Header */}
      <DisclaimerBanner />

      {/* 2. Main Layout (Sidebar + Workspace) */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left Sidebar (260px) */}
        <ThreadSidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          {/* Top Header */}
          <Header />

          {/* Optional Error Alert Toast */}
          {error && (
            <div
              role="alert"
              className="px-4 py-2 text-[13px] flex items-center justify-between z-20 border-b bg-red-50 border-red-200 text-red-800 dark:bg-red-950/80 dark:border-red-900 dark:text-red-200"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
                <span>{error}</span>
              </div>
              <button
                onClick={clearError}
                aria-label="Dismiss error notification"
                className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded-md cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Main Viewport Workspace Split (Left: Feed & Composer, Right: FactSheet on Desktop >= 1100px) */}
          <main className="flex-1 flex overflow-hidden min-h-0">
            {/* Conversation Stream & Composer Column */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
              <MessageFeed />
              <div className="px-4 sm:px-6 pb-2 shrink-0">
                <Composer />
              </div>
            </div>

            {/* Desktop Fact Sheet Panel (Visible when screen >= 1280px / xl) */}
            <aside
              className="hidden xl:flex w-[420px] border-l flex-col overflow-hidden shrink-0 p-5 bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620]"
              aria-label="Scheme fact sheet panel"
            >
              <FactSheetContent />
            </aside>
          </main>

          {/* Clean Site Footer */}
          <Footer />

          {/* Mobile Bottom Sheet & Tablet Drawer (< 1280px) */}
          <FactSheetDrawer />

          {/* About / Details Modal */}
          <AboutModal />
        </div>
      </div>
    </div>
  );
};

export default App;
