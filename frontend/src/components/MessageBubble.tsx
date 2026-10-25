import React from 'react';
import {
  AlertCircle,
  Clock,
  ExternalLink,
  HelpCircle,
  Lock,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';
import type { Message } from '../types/chat';

interface Props {
  message: Message;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[85%] md:max-w-[70%] bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-2xl rounded-tr-xs px-4 py-3 shadow-xs">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
        </div>
      </div>
    );
  }

  // Assistant Message Badging
  const renderBadge = () => {
    switch (message.type) {
      case 'fact_store':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-[#00b386]/10 text-[#00b386] border border-[#00b386]/30 px-2 py-0.5 rounded-full">
            <Zap className="w-3 h-3" />
            Official Database Metric
          </span>
        );
      case 'llm_synthesis':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/30 px-2 py-0.5 rounded-full">
            <Sparkles className="w-3 h-3" />
            Grounded Procedural FAQ
          </span>
        );
      case 'refusal':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full">
            <AlertCircle className="w-3 h-3" />
            Regulatory Compliance Notice
          </span>
        );
      case 'clarification':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full">
            <HelpCircle className="w-3 h-3" />
            Scheme Disambiguation
          </span>
        );
      case 'pii_block':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">
            <ShieldAlert className="w-3 h-3" />
            Security Warning · PII Blocked
          </span>
        );
      case 'not_found':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-gray-500/10 text-gray-600 dark:text-gray-400 border border-gray-500/30 px-2 py-0.5 rounded-full">
            <Lock className="w-3 h-3" />
            Not Found In Records
          </span>
        );
      default:
        return null;
    }
  };

  // Format canonical link label
  const getDomainLabel = (url?: string) => {
    if (!url) return '';
    try {
      const parsed = new URL(url);
      return parsed.hostname.replace('www.', '');
    } catch {
      return 'Official Source';
    }
  };

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[92%] md:max-w-[78%] bg-white dark:bg-[#1E242B] border border-gray-200 dark:border-gray-800 rounded-2xl rounded-tl-xs p-4 shadow-xs">
        {/* Top metadata row */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          {renderBadge()}

          {message.latency_ms !== undefined && (
            <span className="text-[10px] text-gray-400 dark:text-gray-500 font-mono">
              {message.latency_ms < 1000
                ? `${Math.round(message.latency_ms)}ms`
                : `${(message.latency_ms / 1000).toFixed(2)}s`}
            </span>
          )}
        </div>

        {/* Answer body (strictly <= 3 sentences) */}
        <div className="text-sm md:text-base text-gray-800 dark:text-gray-200 leading-relaxed mb-3">
          {message.text}
        </div>

        {/* Citation & Date Footer */}
        <div className="pt-2.5 border-t border-gray-100 dark:border-gray-800/80 flex flex-wrap items-center justify-between gap-2 text-xs">
          {message.citation_url && (
            <a
              href={message.citation_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-medium text-[#00b386] hover:text-[#00d09c] hover:underline"
            >
              <span>Source: {getDomainLabel(message.citation_url)}</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}

          {message.last_updated && (
            <span className="inline-flex items-center gap-1 text-[11px] text-gray-400 dark:text-gray-500 font-mono">
              <Clock className="w-3 h-3" />
              Last updated: {message.last_updated}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
