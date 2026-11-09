import React, { useState } from 'react';
import {
  AlertCircle,
  Check,
  CheckCircle,
  Copy,
  ExternalLink,
  HelpCircle,
  Hourglass,
  Info,
  Link as LinkIcon,
  RotateCcw,
  Shield,
  SlidersHorizontal,
  ThumbsDown,
  ThumbsUp,
} from 'lucide-react';
import { useChatStore } from '../store/useChatStore';
import type { Message } from '../types/chat';

function formatDate(isoStr?: string): string {
  if (!isoStr) return '5 Nov 2026';
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

interface ParsedContent {
  prose: string;
  metrics: { label: string; value: string }[];
  note?: string;
}

function parseAnswerText(rawText: string): ParsedContent {
  const lines = rawText.split('\n');
  const proseLines: string[] = [];
  const metrics: { label: string; value: string }[] = [];
  let note: string | undefined;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Table row parse
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const parts = trimmed.split('|').map((p) => p.trim()).filter(Boolean);
      if (parts.length >= 2) {
        const label = parts[0].replace(/\*\*/g, '').replace(/:---/g, '').trim();
        const value = parts[1].replace(/\*\*/g, '').replace(/:---/g, '').trim();
        if (label && value && !label.toLowerCase().includes('metric') && !label.includes('---')) {
          if (!label.toLowerCase().includes('data source') && !label.toLowerCase().includes('fund house')) {
            metrics.push({ label, value });
          }
        }
      }
    } else if (trimmed.toLowerCase().startsWith('note:')) {
      note = trimmed.replace(/^note:\s*/i, '');
    } else if (trimmed.toLowerCase().startsWith('source:')) {
      // Citation footer ignored in prose body
    } else {
      proseLines.push(trimmed);
    }
  }

  return {
    prose: proseLines.join('\n\n'),
    metrics,
    note,
  };
}

interface Props {
  message: Message;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const { meta, sendUserMessage, submitMessageFeedback, isSending } = useChatStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = (textToCopy: string) => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const asOf = formatDate(message.last_updated);
  const citationUrl = message.citation_url || 'https://groww.in';

  // 1. User Message Bubble
  if (message.role === 'user') {
    return (
      <div className="flex items-start justify-end w-full animate-fade-in">
        <div className="rounded-2xl px-4 py-3 max-w-xl shadow-xs border transition-colors bg-white border-[#E2E8F0] text-[#0F172A] dark:bg-[#242c28] dark:border-[#2f3633] dark:text-[#dde4df]">
          <p className="text-[14px] sm:text-[15px] leading-relaxed whitespace-pre-wrap">
            {message.text}
          </p>
        </div>
      </div>
    );
  }

  // 2. Privacy & Security Warning (HTTP 400 PII or pii_block)
  if (message.type === 'pii_warning' || message.type === 'pii_block') {
    return (
      <div
        role="alert"
        className="w-full rounded-2xl p-4 sm:p-5 shadow-xs flex items-start gap-3.5 border transition-colors bg-amber-50 border-amber-200 dark:bg-amber-950/40 dark:border-amber-900/50 animate-fade-in"
      >
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-amber-100 dark:bg-amber-900/60 text-[#B45309] dark:text-[#ffb95f]">
          <Shield className="w-5 h-5" />
        </div>
        <div className="flex flex-col gap-1 min-w-0">
          <span className="text-[14px] font-bold text-[#92400E] dark:text-[#ffb95f]">
            Privacy &amp; Security Warning
          </span>
          <p className="text-[14px] text-[#92400E] dark:text-[#ffddb8] leading-relaxed">
            Please don&apos;t share PAN, Aadhaar, folio numbers or OTPs. Your message was not processed.
          </p>
        </div>
      </div>
    );
  }

  // 3. Rate Limit Reached (HTTP 429)
  if (message.type === 'rate_limit') {
    return (
      <div
        role="status"
        className="w-full rounded-2xl p-4 sm:p-5 shadow-xs flex items-center justify-between gap-3 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-[#F1F5F9] border border-[#E2E8F0] dark:bg-[#242c28] dark:border-[#2f3633] text-[#475569] dark:text-[#94a3b8]">
            <Hourglass className="w-5 h-5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#dde4df]">
              Rate limit reached
            </span>
            <p className="text-[13px] sm:text-[14px] text-[#475569] dark:text-[#94a3b8] truncate">
              Too many requests. Please wait a minute.
            </p>
          </div>
        </div>
        <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8] font-medium px-2.5 py-1 rounded-md bg-[#F1F5F9] dark:bg-[#16201b] shrink-0">
          Wait ~45s
        </span>
      </div>
    );
  }

  // 4. Timeout Error Card
  if (message.type === 'timeout') {
    return (
      <div
        role="alert"
        className="w-full rounded-2xl p-4 sm:p-5 shadow-xs flex items-center justify-between gap-3 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in"
      >
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-[#B45309] dark:text-[#ffb95f] shrink-0" />
          <span className="text-[14px] text-[#0F172A] dark:text-[#dde4df]">
            Couldn&apos;t answer in time. Please try again.
          </span>
        </div>
        <button
          onClick={() => sendUserMessage('Retry last question')}
          disabled={isSending}
          className="min-h-[44px] px-3.5 py-1.5 rounded-xl text-[13px] font-semibold border flex items-center gap-1.5 transition-colors cursor-pointer bg-[#F8FAFC] border-[#E2E8F0] hover:bg-[#F1F5F9] text-[#0F172A] dark:bg-[#242c28] dark:border-[#2f3633] dark:text-[#dde4df] dark:hover:bg-[#2f3633]"
          type="button"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Try again</span>
        </button>
      </div>
    );
  }

  // 5. Refusal Card ("Can't help with that")
  if (message.type === 'refusal') {
    return (
      <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in">
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-[#F1F5F9] border-[#E2E8F0] text-[#475569] dark:bg-[#16201b] dark:border-[#2f3633] dark:text-[#94a3b8]">
            <Info className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-1 min-w-0">
            <span className="text-[16px] font-bold text-[#0F172A] dark:text-[#dde4df]">
              Can&apos;t help with that
            </span>
            <p className="text-[14px] sm:text-[15px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
              {message.text ||
                'I can only provide objective facts about these schemes. I cannot recommend funds, compare them, or predict returns.'}
            </p>
            <div className="pt-1.5">
              <a
                href="https://www.amfiindia.com/investor-corner"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#059669] dark:text-[#4edea3] hover:underline min-h-[44px]"
              >
                <span>Learn more at AMFI investor education ↗</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 6. Clarification / Disambiguation Card
  if (message.type === 'clarification') {
    const schemes = meta?.schemes || [];
    return (
      <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in">
        <div className="flex items-center gap-2.5">
          <SlidersHorizontal className="w-5 h-5 text-[#059669] dark:text-[#10b981]" />
          <span className="text-[15px] font-bold text-[#0F172A] dark:text-[#dde4df]">
            Which scheme did you mean? Please select one to view its facts:
          </span>
        </div>
        <div className="flex flex-wrap gap-2 pt-1">
          {schemes.map((s) => (
            <button
              key={s.id}
              onClick={() => sendUserMessage(`Show facts for ${s.name}`)}
              disabled={isSending}
              className="min-h-[44px] px-4 py-2 rounded-xl text-[13px] font-medium border transition-colors cursor-pointer bg-[#F8FAFC] border-[#CBD5E1] text-[#0F172A] hover:bg-emerald-50 hover:border-[#059669] hover:text-[#059669] dark:bg-[#16201b] dark:border-[#2f3633] dark:text-[#dde4df] dark:hover:bg-[#242c28] dark:hover:text-[#10b981]"
              type="button"
            >
              {s.name.replace(' (Direct - Growth)', '').replace(' (Direct Growth)', '')}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // 7. Compound Card (Answer portion + Neutral note using backend text unchanged)
  if (message.type === 'compound' || (message.text.includes('Note:') && message.text.includes('Answer'))) {
    const parsed = parseAnswerText(message.text);
    return (
      <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-4 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in">
        {/* Fact Component */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-[#059669] dark:text-[#10b981]" />
              <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#dde4df]">
                Answer
              </span>
            </div>
            <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8]">
              Data as of {asOf}
            </span>
          </div>

          <p className="text-[14px] sm:text-[15px] leading-relaxed text-[#0F172A] dark:text-[#dde4df]">
            {parsed.prose}
          </p>

          {/* Stat Matrix if available */}
          {parsed.metrics.length > 0 && (
            <div className="rounded-xl p-3.5 border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2c25]">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {parsed.metrics.map((m, idx) => (
                  <div key={idx} className="flex flex-col">
                    <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8] mb-0.5">
                      {m.label}
                    </span>
                    <span className="text-[14px] font-semibold text-[#0F172A] dark:text-[#dde4df]">
                      {m.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="w-full h-px bg-[#E2E8F0] dark:bg-[#2f3633]" />

        {/* Neutral note portion using backend text unchanged */}
        <div className="flex items-start gap-2.5 p-3.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b]/70 dark:border-[#1f2c25]">
          <Info className="w-4 h-4 text-[#64748B] dark:text-[#94a3b8] shrink-0 mt-0.5" />
          <p className="text-[13px] sm:text-[14px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
            <strong className="text-[#0F172A] dark:text-[#dde4df]">Note:</strong>{' '}
            {parsed.note ||
              'I can only provide objective facts about these schemes. I cannot evaluate market timing or recommend whether to invest now.'}
          </p>
        </div>

        {/* Action Footer */}
        <div className="flex flex-wrap items-center justify-between pt-1 gap-3">
          <a
            href={citationUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[13px] font-semibold transition-colors min-h-[44px] bg-[#F8FAFC] border-[#E2E8F0] text-[#059669] hover:bg-emerald-50 dark:bg-[#16201b] dark:border-[#1f2824] dark:text-[#10b981] dark:hover:bg-[#242c28]"
          >
            <LinkIcon className="w-3.5 h-3.5" />
            <span>Source: Groww scheme page · Data as of {asOf}</span>
          </a>
          <button
            onClick={() => handleCopy(parsed.prose)}
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#dde4df] min-h-[44px] px-2 cursor-pointer"
            type="button"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>{copied ? 'Copied!' : 'Copy fact'}</span>
          </button>
        </div>
      </div>
    );
  }

  // 8. Neutral Info Card (out_of_scope / not_found / unsupported_plan / external_amc / help)
  if (
    message.type === 'not_found' ||
    message.type === 'out_of_scope' ||
    message.type === 'unsupported_plan' ||
    message.type === 'external_amc' ||
    message.type === 'help' ||
    message.type === 'glossary'
  ) {
    const title =
      message.type === 'out_of_scope' || message.type === 'external_amc'
        ? 'Out of scope query'
        : message.type === 'unsupported_plan'
        ? 'Direct Plan Scope'
        : message.type === 'help'
        ? 'Fund Scope & Guidance'
        : message.type === 'glossary'
        ? 'Glossary Definition'
        : 'Information not found';

    return (
      <div className="w-full rounded-2xl p-5 shadow-sm flex items-start gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-[#F8FAFC] border-[#E2E8F0] text-[#475569] dark:bg-[#16201b] dark:border-[#2f3633] dark:text-[#94a3b8]">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div className="flex flex-col gap-1 min-w-0">
          <span className="text-[15px] font-bold text-[#0F172A] dark:text-[#dde4df]">
            {title}
          </span>
          <p className="text-[14px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
            {message.text || 'I can only answer factual questions about these 5 HDFC schemes.'}
          </p>
        </div>
      </div>
    );
  }

  // 9. Standard Answer Card (fact_store / llm_synthesis / answer)
  const parsed = parseAnswerText(message.text);

  return (
    <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-4 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620] animate-fade-in">
      {/* Top Bar: Check icon badge + "Answer" + "Data as of <as_of>" */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md flex items-center justify-center font-bold bg-emerald-100 text-[#059669] dark:bg-[#10b981] dark:text-[#003824]">
            <Check className="w-4 h-4 stroke-[3]" />
          </div>
          <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#dde4df]">
            Answer
          </span>
        </div>
        <span className="text-[13px] font-medium text-[#64748B] dark:text-[#94a3b8]">
          Data as of {asOf}
        </span>
      </div>

      {/* Narrative Prose */}
      <div className="text-[14px] sm:text-[15px] leading-relaxed text-[#0F172A] dark:text-[#dde4df]">
        <p className="whitespace-pre-wrap">{parsed.prose || message.text}</p>
      </div>

      {/* Stat Matrix (Grid with no cell truncation) */}
      {parsed.metrics.length > 0 && (
        <div className="rounded-xl p-4 border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2c25]">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
            {parsed.metrics.map((m, idx) => (
              <div key={idx} className="flex flex-col">
                <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8] mb-0.5">
                  {m.label}
                </span>
                <span className="text-[14px] font-semibold text-[#0F172A] dark:text-[#dde4df] leading-snug">
                  {m.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Footer */}
      <div className="flex flex-wrap items-center justify-between pt-1 gap-3">
        {/* Source Link */}
        <a
          href={citationUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[13px] font-semibold transition-colors min-h-[44px] bg-[#F8FAFC] border-[#E2E8F0] text-[#059669] hover:bg-emerald-50 dark:bg-[#16201b] dark:border-[#1f2824] dark:text-[#10b981] dark:hover:bg-[#242c28]"
        >
          <LinkIcon className="w-3.5 h-3.5" />
          <span>Source: Groww scheme page · Data as of {asOf}</span>
        </a>

        {/* Action Controls: Thumbs Up / Down / Copy / Report */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 p-0.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
            <button
              onClick={() => submitMessageFeedback(message.id, 'up')}
              className={`w-9 h-9 flex items-center justify-center rounded-lg transition-colors cursor-pointer ${
                message.userFeedback === 'up'
                  ? 'text-[#059669] bg-emerald-50 dark:text-[#10b981] dark:bg-[#242c28]'
                  : 'text-[#64748B] hover:text-[#059669] dark:text-[#94a3b8] dark:hover:text-[#10b981]'
              }`}
              title="Helpful answer"
              type="button"
              aria-label="Mark helpful"
            >
              <ThumbsUp className="w-4 h-4" />
            </button>
            <button
              onClick={() => submitMessageFeedback(message.id, 'down')}
              className={`w-9 h-9 flex items-center justify-center rounded-lg transition-colors cursor-pointer ${
                message.userFeedback === 'down'
                  ? 'text-red-500 bg-red-50 dark:text-red-400 dark:bg-[#242c28]'
                  : 'text-[#64748B] hover:text-red-500 dark:text-[#94a3b8] dark:hover:text-red-400'
              }`}
              title="Not helpful"
              type="button"
              aria-label="Mark unhelpful"
            >
              <ThumbsDown className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleCopy(parsed.prose || message.text)}
              className="w-9 h-9 flex items-center justify-center rounded-lg text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#dde4df] transition-colors cursor-pointer"
              title="Copy to clipboard"
              type="button"
              aria-label="Copy answer"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => submitMessageFeedback(message.id, 'reported')}
            className="text-[13px] text-[#64748B] hover:text-[#92400E] dark:text-[#94a3b8] dark:hover:text-[#ffb95f] underline decoration-dotted min-h-[44px] cursor-pointer"
            type="button"
          >
            {message.userFeedback === 'reported' ? 'Report submitted' : 'Report incorrect answer'}
          </button>
        </div>
      </div>
    </div>
  );
};
