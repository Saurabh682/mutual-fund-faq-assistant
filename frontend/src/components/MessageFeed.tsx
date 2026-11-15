import React, { useEffect, useRef, useState } from 'react';
import { parseAnswerText } from '../lib/answerText';
import { useChatStore } from '../store/useChatStore';
import { MessageBubble } from './MessageBubble';
import { StarterQuestions } from './StarterQuestions';
import { StaleBanner } from './StaleBanner';

export const MessageFeed: React.FC = () => {
  const { activeThread, isSending } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const seen = useRef<{ thread?: string; count: number }>({ count: 0 });
  const [announcement, setAnnouncement] = useState('');

  const messages = activeThread?.messages || [];
  const hasMessages = messages.length > 0;

  useEffect(() => {
    if (!hasMessages) {
      // An empty chat shows the welcome board: start at its heading, not at the bottom of it
      containerRef.current?.scrollTo?.({ top: 0 });
      return;
    }
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [hasMessages, messages.length, isSending]);

  // Tell screen-reader users when an answer arrives (not when an old thread is opened)
  useEffect(() => {
    const threadId = activeThread?.id;
    const last = messages[messages.length - 1];
    if (seen.current.thread === threadId && messages.length > seen.current.count && last?.role === 'assistant') {
      const parsed = parseAnswerText(last.text);
      setAnnouncement((parsed.prose || last.text).slice(0, 400));
    }
    seen.current = { thread: threadId, count: messages.length };
  }, [activeThread?.id, messages.length]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-5">
      <div className="sr-only" role="status" aria-live="polite">
        {announcement}
      </div>

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
          className="w-full rounded-2xl p-5 shadow-xs flex flex-col gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in"
        >
          <div className="flex items-center gap-2.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#0D9488] dark:bg-[#6ee7b7] animate-ping" />
            <span className="text-[14px] sm:text-[15px] font-semibold text-[#0D9488] dark:text-[#6ee7b7]">
              Checking sources...
            </span>
          </div>
          <div className="space-y-2.5 animate-pulse pt-1">
            <div className="h-4 rounded-md w-5/6 bg-[#E2E8F0] dark:bg-[#2d353b]" />
            <div className="h-4 rounded-md w-3/4 bg-[#E2E8F0] dark:bg-[#2d353b]" />
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="h-10 rounded-lg bg-[#E2E8F0] dark:bg-[#2d353b]" />
              <div className="h-10 rounded-lg bg-[#E2E8F0] dark:bg-[#2d353b]" />
              <div className="h-10 rounded-lg bg-[#E2E8F0] dark:bg-[#2d353b]" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} className="h-2" />
    </div>
  );
};
