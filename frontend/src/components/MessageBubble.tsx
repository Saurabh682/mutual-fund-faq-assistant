import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Check,
  Copy,
  ExternalLink,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';
import type { Message } from '../types/chat';

interface Props {
  message: Message;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatCitation = (url?: string) => {
    if (!url) return 'groww.in';
    try {
      const parsed = new URL(url);
      const parts = parsed.pathname.split('/').filter(Boolean);
      return `${parsed.hostname}/${parts.slice(0, 2).join('/')}...`;
    } catch {
      return url;
    }
  };

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const renderFormattedText = (content: string) => {
    if (!content.includes('|')) {
      return <p className="text-sm text-slate-100 leading-relaxed whitespace-pre-wrap">{content}</p>;
    }

    const lines = content.split('\n');
    const blocks: { type: 'text' | 'table'; lines: string[] }[] = [];
    let currentBlock: { type: 'text' | 'table'; lines: string[] } | null = null;

    for (const line of lines) {
      const isTableLine = line.trim().startsWith('|') && line.trim().endsWith('|');
      if (isTableLine) {
        if (currentBlock?.type === 'table') {
          currentBlock.lines.push(line);
        } else {
          if (currentBlock) blocks.push(currentBlock);
          currentBlock = { type: 'table', lines: [line] };
        }
      } else {
        if (currentBlock?.type === 'text') {
          currentBlock.lines.push(line);
        } else {
          if (currentBlock) blocks.push(currentBlock);
          currentBlock = { type: 'text', lines: [line] };
        }
      }
    }
    if (currentBlock) blocks.push(currentBlock);

    const cleanCell = (c: string) =>
      c.trim().replace(/^\*\*(.*?)\*\*$/, '$1').replace(/^\*(.*?)\*$/, '$1');

    return (
      <div className="space-y-3">
        {blocks.map((block, idx) => {
          if (block.type === 'text') {
            const text = block.lines.join('\n').trim();
            if (!text) return null;
            return (
              <p key={idx} className="text-sm text-slate-100 leading-relaxed whitespace-pre-wrap">
                {text}
              </p>
            );
          }

          const headerLine = block.lines[0];
          const dataRows = block.lines.slice(2);
          const headers = headerLine.split('|').slice(1, -1).map(cleanCell);

          return (
            <div key={idx} className="overflow-x-auto my-2.5 rounded-xl border border-[#28323E] bg-[#12161A]/90 shadow-md">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#28323E] bg-[#1E252E]/90 text-slate-300 font-semibold">
                    {headers.map((h, hIdx) => (
                      <th key={hIdx} className="px-3.5 py-2 font-semibold text-slate-300 first:w-1/3">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#28323E]/60 text-slate-200">
                  {dataRows.map((r, rIdx) => {
                    const cells = r.split('|').slice(1, -1).map(cleanCell);
                    return (
                      <tr key={rIdx} className="hover:bg-[#1E252E]/40 transition-colors">
                        {cells.map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            className={`px-3.5 py-2.5 ${
                              cIdx === 0
                                ? 'font-medium text-slate-300'
                                : 'font-semibold text-[#00D09C] font-mono'
                            }`}
                          >
                            {cell}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        })}
      </div>
    );
  };

  // 1. User Message Bubble
  if (isUser) {
    return (
      <div className="flex justify-end items-start gap-3 mb-4">
        <div className="flex flex-col items-end max-w-[85%] sm:max-w-[70%]">
          <div className="bg-[#242D38] border border-[#28323E] rounded-2xl rounded-tr-xs px-4 py-3 text-sm text-white shadow-md">
            {message.text}
          </div>
          <span className="text-[10px] text-slate-500 mt-1 font-mono">
            {formatTime(message.timestamp)} • User Query
          </span>
        </div>
        <div className="w-7 h-7 rounded-full bg-[#1A2027] border border-[#28323E] flex items-center justify-center text-xs text-slate-300 font-semibold shrink-0 mt-0.5">
          U
        </div>
      </div>
    );
  }

  // 2. Assistant Refusal Bubble (Advisory or Comparative query)
  if (message.type === 'refusal') {
    return (
      <div className="flex justify-start items-start gap-3 mb-4">
        <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 mt-0.5 shadow-sm">
          <AlertTriangle className="w-4 h-4" />
        </div>

        <div className="flex flex-col max-w-[90%] sm:max-w-[80%] gap-2">
          <div className="bg-[#1A2027] border border-amber-500/40 rounded-2xl rounded-tl-xs p-4 sm:p-5 shadow-lg relative">
            <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-[#28323E]/80">
              <div className="flex items-center gap-1.5 text-xs text-amber-400 font-semibold">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>SEBI Compliance Refusal (No Investment Advice)</span>
              </div>
              <span className="text-[10px] font-mono text-amber-300/80 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                Rule 7A Regulated
              </span>
            </div>

            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {message.text}
            </p>

            {message.citation_url && (
              <div className="mt-4 pt-3 border-t border-[#28323E] flex flex-wrap items-center gap-2">
                <a
                  href={message.citation_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-amber-300 hover:text-amber-200 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 px-3 py-1 rounded-full font-medium transition"
                >
                  <span>📚 AMFI Investor Education Center</span>
                  <span>↗</span>
                </a>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 px-1 text-[11px] text-slate-500 font-mono">
            <span className="text-amber-400 font-medium">System Guardrail Triggered: Intent(Advisory_Refusal)</span>
          </div>
        </div>
      </div>
    );
  }

  // 3. Assistant PII Security Warning Bubble
  if (message.type === 'pii_block') {
    return (
      <div className="flex justify-start items-start gap-3 mb-4">
        <div className="w-8 h-8 rounded-xl bg-red-500/10 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0 mt-0.5 shadow-sm">
          <ShieldAlert className="w-4 h-4" />
        </div>

        <div className="flex flex-col max-w-[90%] sm:max-w-[80%] gap-2">
          <div className="bg-[#1A2027] border border-red-500/40 rounded-2xl rounded-tl-xs p-4 sm:p-5 shadow-lg relative">
            <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-[#28323E]/80">
              <div className="flex items-center gap-1.5 text-xs text-red-400 font-semibold">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>DPDP Act 2023 Security Notice</span>
              </div>
              <span className="text-[10px] font-mono text-red-300/80 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                PII Blocked
              </span>
            </div>

            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {message.text}
            </p>
          </div>

          <div className="flex items-center gap-2 px-1 text-[11px] text-red-400 font-mono">
            <span>Query blocked at firewall before LLM processing.</span>
          </div>
        </div>
      </div>
    );
  }

  // 4. Assistant Factual / RAG Answer Bubble
  const isFactStore = message.type === 'fact_store';
  const badgeLabel = isFactStore
    ? 'Facts Grounded: Official Fact Store'
    : 'Facts Grounded: Verified Groww Corpus';

  return (
    <div className="flex justify-start items-start gap-3 mb-4">
      <div className="w-8 h-8 rounded-xl bg-[#00D09C]/10 border border-[#00D09C]/40 flex items-center justify-center text-[#00D09C] shrink-0 mt-0.5 shadow-sm">
        {isFactStore ? (
          <Zap className="w-4 h-4 stroke-[2.2]" />
        ) : (
          <Sparkles className="w-4 h-4 stroke-[2.2]" />
        )}
      </div>

      <div className="flex flex-col max-w-[90%] sm:max-w-[80%] gap-2">
        <div className="bg-[#1A2027] border border-[#00D09C]/35 rounded-2xl rounded-tl-xs p-4 sm:p-5 shadow-lg relative">
          {/* Top Verification Header */}
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#28323E]/80">
            <div className="flex items-center gap-1.5 text-xs text-[#00D09C] font-semibold">
              <span className="w-2 h-2 rounded-full bg-[#00D09C]"></span>
              <span>{badgeLabel}</span>
            </div>
            {message.latency_ms && (
              <span className="text-[10px] font-mono text-slate-400 bg-[#12161A] px-2 py-0.5 rounded border border-[#28323E]">
                {message.latency_ms.toFixed(1)}ms
              </span>
            )}
          </div>

          {/* Authoritative Answer Text */}
          {renderFormattedText(message.text)}

          {/* Single Citation Pill & Action Buttons */}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-[#28323E]">
            {message.citation_url ? (
              <a
                href={message.citation_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-[#00D09C] hover:text-[#00B386] bg-[#00D09C]/10 hover:bg-[#00D09C]/20 border border-[#00D09C]/30 px-2.5 py-1 rounded-full font-medium transition group"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Source: {formatCitation(message.citation_url)}</span>
                <span className="group-hover:translate-x-0.5 transition-transform">↗</span>
              </a>
            ) : (
              <div />
            )}

            <div className="flex items-center gap-1 text-slate-400">
              <button
                onClick={handleCopy}
                className="p-1 hover:text-white rounded hover:bg-[#12161A] transition cursor-pointer"
                title={copied ? 'Copied!' : 'Copy answer'}
              >
                {copied ? <Check className="w-3.5 h-3.5 text-[#00D09C]" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Freshness Footer Invariant */}
        {message.last_updated && (
          <div className="flex items-center gap-2 px-1 text-[11px] text-slate-500 font-mono">
            <span className="flex items-center gap-1 text-emerald-400">
              <Check className="w-3 h-3 stroke-[2.5]" />
              Verified O(1) Fact Store
            </span>
            <span>•</span>
            <span>
              Last updated from sources: <span className="text-slate-400 font-semibold">{message.last_updated}</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
