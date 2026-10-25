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
          <div className="w-8 h-8 border-3 border-[#00b386] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-gray-400">Loading conversation...</p>
        </div>
      </div>
    );
  }

  const messages = activeThread?.messages || [];

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col justify-center overflow-y-auto">
        <StarterQuestions />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 max-w-4xl w-full mx-auto">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isSending && (
        <div className="flex justify-start mb-4">
          <div className="bg-white dark:bg-[#1E242B] border border-gray-200 dark:border-gray-800 rounded-2xl rounded-tl-xs px-4 py-3 shadow-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#00b386] animate-pulse" />
              <span className="w-2 h-2 rounded-full bg-[#00b386] animate-pulse [animation-delay:200ms]" />
              <span className="w-2 h-2 rounded-full bg-[#00b386] animate-pulse [animation-delay:400ms]" />
              <span className="text-xs text-gray-400 ml-2">Verifying official records...</span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
