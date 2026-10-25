import React from 'react';
import { ArrowUpRight, HelpCircle } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

const DEFAULT_STARTERS = [
  'What is the exit load for HDFC Mid-Cap Opportunities Fund?',
  'What is the minimum SIP amount for HDFC Small Cap Fund?',
  'How to redeem HDFC Small Cap Fund units?',
];

export const StarterQuestions: React.FC = () => {
  const { meta, sendUserMessage, isSending } = useChatStore();
  const questions = meta?.starter_questions && meta.starter_questions.length > 0
    ? meta.starter_questions
    : DEFAULT_STARTERS;

  const handleChipClick = (q: string) => {
    if (!isSending) {
      sendUserMessage(q);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto py-8 px-4 text-center">
      <div className="w-12 h-12 rounded-2xl bg-[#00b386]/10 border border-[#00b386]/30 flex items-center justify-center mx-auto mb-4 text-[#00b386] shadow-sm">
        <HelpCircle className="w-6 h-6" />
      </div>

      <h2 className="text-lg md:text-xl font-bold text-gray-900 dark:text-white mb-2">
        How can I help you today?
      </h2>
      <p className="text-xs md:text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
        Ask objective, factual questions about expense ratios, minimum investments, exit loads, or redemption procedures.
      </p>

      <div className="grid grid-cols-1 gap-2.5 text-left">
        {questions.map((q, idx) => (
          <button
            key={idx}
            disabled={isSending}
            onClick={() => handleChipClick(q)}
            className="flex items-center justify-between p-3.5 rounded-xl bg-white dark:bg-[#1E242B] border border-gray-200 dark:border-gray-700/70 hover:border-[#00b386] dark:hover:border-[#00b386] hover:bg-gray-50 dark:hover:bg-[#1E242B]/80 text-sm font-medium text-gray-800 dark:text-gray-200 transition shadow-xs group cursor-pointer disabled:opacity-50"
          >
            <span className="pr-4">{q}</span>
            <ArrowUpRight className="w-4 h-4 text-gray-400 group-hover:text-[#00b386] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
};
