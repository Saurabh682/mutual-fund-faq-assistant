import React, { useEffect, useRef } from 'react';
import { useChatStore } from '../store/useChatStore';
import { MessageBubble } from './MessageBubble';
import { StarterQuestions } from './StarterQuestions';

export const MessageFeed: React.FC = () => {
  const { activeThread, isSending, isLoadingMessages } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeThread?.messages, isSending]);

  if (isLoadingMessages) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-2 border-[#00D09C] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400 font-mono">Accessing official SQLite and ChromaDB records...</p>
        </div>
      </div>
    );
  }

  const messages = activeThread?.messages || [];

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6">
      <div className="max-w-[860px] mx-auto flex flex-col gap-4">
        {messages.length === 0 ? (
          <StarterQuestions />
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}

        {isSending && (
          <div className="flex justify-start items-start gap-3 mb-4">
            <div className="w-8 h-8 rounded-xl bg-[#00D09C]/10 border border-[#00D09C]/40 flex items-center justify-center text-[#00D09C] shrink-0 mt-0.5 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#00D09C] animate-ping" />
            </div>
            <div className="bg-[#1A2027] border border-[#28323E] rounded-2xl rounded-tl-xs px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#00D09C] animate-pulse" />
                <span className="w-2 h-2 rounded-full bg-[#00D09C] animate-pulse [animation-delay:200ms]" />
                <span className="w-2 h-2 rounded-full bg-[#00D09C] animate-pulse [animation-delay:400ms]" />
                <span className="text-xs text-slate-400 font-mono ml-2">Verifying scheme records &amp; facts...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
};
