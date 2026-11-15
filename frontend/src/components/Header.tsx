import React, { useState, useRef, useEffect } from 'react';
import {
  Calendar,
  ChevronDown,
  FileText,
  Info,
  Menu,
  MoreVertical,
  ShieldAlert,
  User,
} from 'lucide-react';
import { formatDate } from '../lib/format';
import { useChatStore } from '../store/useChatStore';
import { groupByFundHouse } from '../lib/schemes';

export const Header: React.FC = () => {
  const {
    meta,
    schemeFacts,
    factsState,
    selectedSchemeId,
    setSelectedSchemeId,
    toggleFactSheet,
    toggleSidebar,
    setAboutModalOpen,
  } = useChatStore();

  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
  const moreMenuRef = useRef<HTMLDivElement>(null);

  // Close more menu when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (moreMenuRef.current && !moreMenuRef.current.contains(e.target as Node)) {
        setIsMoreMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const schemes = meta?.schemes || [];
  const currentSchemeFacts = schemeFacts.find((s) => s.scheme_id === selectedSchemeId);
  const asOfDate =
    typeof currentSchemeFacts?.as_of === 'string'
      ? currentSchemeFacts.as_of
      : typeof currentSchemeFacts?.ter_direct?.as_of === 'string'
      ? currentSchemeFacts.ter_direct.as_of
      : '';

  return (
    <header className="w-full h-16 px-4 sm:px-6 flex items-center justify-between gap-3 border-b shadow-xs sticky top-0 z-20 backdrop-blur-md bg-white/95 border-[#E2E8F0] dark:bg-[#0e1512]/95 dark:border-[#1a231f] transition-colors">
      {/* Left: Mobile menu toggle + Scheme selector strictly on a single line */}
      <div className="flex items-center gap-2.5 sm:gap-3 min-w-0 max-w-[65%] sm:max-w-[70%]">
        <button
          onClick={toggleSidebar}
          aria-label="Toggle navigation menu"
          className="lg:hidden min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl text-[#475569] hover:text-[#0F172A] hover:bg-[#F1F5F9] dark:text-[#94a3b8] dark:hover:text-[#dde4df] dark:hover:bg-[#16201b] transition-colors cursor-pointer shrink-0"
          type="button"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Scheme Selector kept strictly on a single line with truncate */}
        <div className="relative min-w-0 shrink">
          <label htmlFor="scheme-header-select" className="sr-only">
            Select Scheme
          </label>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border transition-colors bg-[#F8FAFC] border-[#E2E8F0] hover:bg-[#F1F5F9] dark:bg-[#16201b] dark:border-[#1f2824] dark:hover:bg-[#242c28] cursor-pointer max-w-full min-w-0">
            <span className="w-2 h-2 rounded-full bg-[#047857] dark:bg-[#10b981] shrink-0" />
            <select
              id="scheme-header-select"
              value={selectedSchemeId}
              onChange={(e) => setSelectedSchemeId(e.target.value)}
              disabled={schemes.length === 0}
              className="min-w-0 flex-1 bg-transparent text-[13px] sm:text-[14px] font-semibold text-[#0F172A] dark:text-[#dde4df] focus:outline-none cursor-pointer truncate max-w-[180px] sm:max-w-[280px] md:max-w-[340px] pr-2 appearance-none"
            >
              {schemes.length === 0 && <option value="">Loading schemes…</option>}
              {groupByFundHouse(schemes).map((g) => (
                <optgroup key={g.house} label={g.house || 'Schemes'}>
                  {g.schemes.map((s) => (
                <option
                  key={s.id}
                  value={s.id}
                  className="bg-white text-[#0F172A] dark:bg-[#16201b] dark:text-[#dde4df]"
                >
                  {s.name}
                </option>
              ))}
                </optgroup>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[#64748B] dark:text-[#94a3b8] shrink-0 pointer-events-none" />
          </div>
        </div>

        {/* Scheme fact sheet button */}
        <button
          onClick={() => toggleFactSheet()}
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-[13px] font-medium border transition-colors cursor-pointer shrink-0 bg-white border-[#E2E8F0] text-[#475569] hover:bg-[#F8FAFC] hover:text-[#0F172A] dark:bg-[#16201b] dark:border-[#1f2824] dark:text-[#dde4df] dark:hover:bg-[#242c28] min-h-[44px]"
          type="button"
          aria-label="Toggle scheme fact sheet drawer"
        >
          <FileText className="w-4 h-4 text-[#047857] dark:text-[#10b981]" />
          <span>Scheme fact sheet</span>
        </button>
      </div>

      {/* Right: Data Date, More menu, User avatar */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {/* Data As Of Chip */}
        {asOfDate ? (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-[13px] font-medium bg-[#F8FAFC] border-[#E2E8F0] text-[#64748B] dark:bg-[#16201b] dark:border-[#1f2824] dark:text-[#94a3b8]">
            <Calendar className="w-3.5 h-3.5 text-[#047857] dark:text-[#10b981]" />
            <span>Data as of {formatDate(asOfDate)}</span>
          </div>
        ) : (
          factsState === 'loading' && (
            <div aria-hidden="true" className="hidden md:block h-8 w-44 rounded-lg animate-pulse bg-[#E2E8F0] dark:bg-[#242c28]" />
          )
        )}

        {/* More Dropdown */}
        <div className="relative" ref={moreMenuRef}>
          <button
            onClick={() => setIsMoreMenuOpen((prev) => !prev)}
            aria-expanded={isMoreMenuOpen}
            aria-label="More options"
            className="min-h-[44px] min-w-[44px] flex items-center justify-center gap-1 px-2.5 py-1.5 rounded-xl border text-[13px] font-medium transition-colors cursor-pointer bg-white border-[#E2E8F0] text-[#475569] hover:text-[#0F172A] hover:bg-[#F8FAFC] dark:bg-[#16201b] dark:border-[#1f2824] dark:text-[#94a3b8] dark:hover:text-[#dde4df] dark:hover:bg-[#242c28]"
            type="button"
          >
            <span className="hidden sm:inline">More</span>
            <MoreVertical className="w-4 h-4 sm:hidden" />
            <ChevronDown className="w-3.5 h-3.5 hidden sm:inline" />
          </button>

          {isMoreMenuOpen && (
            <div className="absolute right-0 mt-2 w-52 rounded-xl shadow-xl border py-1.5 z-40 animate-fade-in bg-white border-[#E2E8F0] text-[#0F172A] dark:bg-[#16201b] dark:border-[#2f3633] dark:text-[#dde4df]">
              <button
                onClick={() => {
                  setIsMoreMenuOpen(false);
                  toggleFactSheet(true);
                }}
                className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-[13px] text-left hover:bg-[#F1F5F9] dark:hover:bg-[#242c28] transition-colors cursor-pointer min-h-[44px]"
              >
                <FileText className="w-4 h-4 text-[#047857] dark:text-[#10b981]" />
                <span>Scheme Fact Sheet</span>
              </button>
              <button
                onClick={() => {
                  setIsMoreMenuOpen(false);
                  setAboutModalOpen(true);
                }}
                className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-[13px] text-left hover:bg-[#F1F5F9] dark:hover:bg-[#242c28] transition-colors cursor-pointer min-h-[44px]"
              >
                <Info className="w-4 h-4 text-[#475569] dark:text-[#94a3b8]" />
                <span>About FundFacts</span>
              </button>
              <a
                href="https://groww.in"
                target="_blank"
                rel="noreferrer"
                onClick={() => setIsMoreMenuOpen(false)}
                className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-[13px] text-left hover:bg-[#F1F5F9] dark:hover:bg-[#242c28] transition-colors cursor-pointer min-h-[44px]"
              >
                <ShieldAlert className="w-4 h-4 text-[#B45309] dark:text-[#ffb95f]" />
                <span>Source scheme portal ↗</span>
              </a>
            </div>
          )}
        </div>

        {/* User Avatar */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-white shadow-xs shrink-0 bg-[#047857] dark:bg-[#10b981] dark:text-[#003824]"
          title="Guest User"
        >
          <User className="w-4 h-4" />
        </div>
      </div>
    </header>
  );
};
