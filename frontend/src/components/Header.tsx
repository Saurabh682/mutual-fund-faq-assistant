import React from 'react';
import { Menu, MessageSquare, TrendingUp } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const Header: React.FC = () => {
  const { toggleSidebar } = useChatStore();

  return (
    <header className="w-full bg-white dark:bg-[#12161A] border-b border-gray-200 dark:border-gray-800 px-4 py-3 shrink-0">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="md:hidden p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-[#00b386]"
            aria-label="Toggle Navigation Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#00b386] to-[#00d09c] flex items-center justify-center text-white shadow-sm shadow-[#00b386]/30">
              <TrendingUp className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <h1 className="text-base md:text-lg font-bold text-gray-900 dark:text-white leading-tight flex items-center gap-2">
                Mutual Fund FAQ Assistant
                <span className="text-[10px] font-semibold bg-[#00b386]/10 text-[#00b386] border border-[#00b386]/30 px-1.5 py-0.2 rounded">
                  OFFICIAL
                </span>
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">
                Authoritative Groww-Verified Facts for HDFC Schemes
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden lg:flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800/80 px-3 py-1.5 rounded-full border border-gray-200 dark:border-gray-700">
            <MessageSquare className="w-3.5 h-3.5 text-[#00b386]" />
            <span>Single Citation · $\le$ 3 Sentences · Grounded</span>
          </div>
        </div>
      </div>
    </header>
  );
};
