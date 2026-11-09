import React from 'react';
import { History } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

function formatDate(isoStr?: string): string {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
  } catch {
    return isoStr;
  }
}

export const StaleBanner: React.FC = () => {
  const { schemeFacts, selectedSchemeId } = useChatStore();

  const currentSchemeFacts = schemeFacts.find((s) => s.scheme_id === selectedSchemeId);
  const rawDate: string | undefined =
    typeof currentSchemeFacts?.as_of === 'string'
      ? currentSchemeFacts.as_of
      : typeof currentSchemeFacts?.ter_direct?.as_of === 'string'
      ? currentSchemeFacts.ter_direct.as_of
      : undefined;

  if (!rawDate) return null;

  const parsedDate = new Date(rawDate);
  if (isNaN(parsedDate.getTime())) return null;

  const diffMs = Date.now() - parsedDate.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);

  // Triggered ONLY when as_of is older than 7 days from API data
  if (diffDays <= 7) return null;

  return (
    <div
      role="status"
      className="w-full px-4 py-2.5 rounded-xl border flex items-center justify-between text-[13px] transition-colors bg-amber-50 border-amber-200 text-[#92400E] dark:bg-[#242c28] dark:border-[#2b3a32] dark:text-[#ffb95f]"
    >
      <div className="flex items-center gap-2">
        <History className="w-4 h-4 shrink-0 text-[#B45309] dark:text-[#ffb95f]" />
        <span className="font-semibold">Notice:</span>
        <span className="text-[#78350F] dark:text-[#dde4df]">
          Data is older than 7 days (as of {formatDate(rawDate)})
        </span>
      </div>
    </div>
  );
};
