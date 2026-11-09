import React, { useEffect, useRef } from 'react';
import { useChatStore } from '../store/useChatStore';
import { MessageBubble } from './MessageBubble';
import { StarterQuestions } from './StarterQuestions';
import { StaleBanner } from './StaleBanner';

export const MessageFeed: React.FC = () => {
  const { activeThread, isSending } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  const messages = activeThread?.messages || [];
  const hasMessages = messages.length > 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, isSending]);

  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-5">
      {/* Dynamic Stale Data Banner (triggers only if >7 days old from API data) */}
      <StaleBanner />

      {/* Empty State / Query Starter Board */}
      {!hasMessages && <StarterQuestions />}

      {/* Message Stream */}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {/* Runtime Checking Sources Skeleton State */}
      {isSending && (
        <div
          role="status"
          aria-live="polite"
          className="w-full rounded-2xl p-5 shadow-xs flex flex-col gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in"
        >
          <div className="flex items-center gap-2.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#059669] dark:bg-[#10b981] animate-ping" />
            <span className="text-[14px] sm:text-[15px] font-semibold text-[#059669] dark:text-[#10b981]">
              Checking sources...
            </span>
          </div>
          <div className="space-y-2.5 animate-pulse pt-1">
            <div className="h-4 rounded-md w-5/6 bg-[#E2E8F0] dark:bg-[#242c28]" />
            <div className="h-4 rounded-md w-3/4 bg-[#E2E8F0] dark:bg-[#242c28]" />
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="h-10 rounded-lg bg-[#E2E8F0] dark:bg-[#242c28]" />
              <div className="h-10 rounded-lg bg-[#E2E8F0] dark:bg-[#242c28]" />
              <div className="h-10 rounded-lg bg-[#E2E8F0] dark:bg-[#242c28]" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} className="h-2" />
    </div>
  );
};
