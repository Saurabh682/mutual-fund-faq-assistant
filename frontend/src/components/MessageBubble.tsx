import React, { useState } from 'react';
import {
  AlertCircle,
  Check,
  CheckCircle,
  ChevronRight,
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
import { parseAnswerText } from '../lib/answerText';
import { formatDate, groupIndian } from '../lib/format';
import type { Message } from '../types/chat';
import { shortSchemeName } from '../lib/schemes';

const NO_INFO_PREFIX = "I don't have that information";

interface Props {
  message: Message;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const { meta, schemeFacts, activeThread, sendUserMessage, submitMessageFeedback, isSending } = useChatStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = (textToCopy: string) => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const asOf = formatDate(message.last_updated);
  const dataAsOf = asOf ? `Data as of ${asOf}` : '';
  const sourceLabel = `Source: Groww scheme page${asOf ? ` · Data as of ${asOf}` : ''}`;
  // The question to ask again if an answer timed out
  const lastQuestion = [...(activeThread?.messages ?? [])].reverse().find((m) => m.role === 'user')?.text;
  // A "no information" reply is not a sourced answer, whatever type an older saved message carries
  const isNoInfoAnswer =
    (message.type === 'llm_synthesis' || message.type === 'answer') && message.text.trim().startsWith(NO_INFO_PREFIX);
  const citationUrl = message.citation_url || 'https://groww.in';

  // 1. User Message Bubble
  if (message.role === 'user') {
    return (
      <div className="flex items-start justify-end w-full animate-fade-in">
        <div className="rounded-2xl px-4 py-3 max-w-xl shadow-xs border transition-colors bg-white border-[#E2E8F0] text-[#0F172A] dark:bg-[#2d353b] dark:border-[#2d353b] dark:text-[#f1f5f9]">
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
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-amber-100 dark:bg-amber-900/60 text-[#B45309] dark:text-[#fcd34d]">
          <Shield className="w-5 h-5" />
        </div>
        <div className="flex flex-col gap-1 min-w-0">
          <span className="text-[14px] font-bold text-[#92400E] dark:text-[#fcd34d]">
            Privacy &amp; Security Warning
          </span>
          <p className="text-[14px] text-[#92400E] dark:text-[#fde68a] leading-relaxed">
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
        className="w-full rounded-2xl p-4 sm:p-5 shadow-xs flex items-center justify-between gap-3 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-[#F1F5F9] border border-[#E2E8F0] dark:bg-[#2d353b] dark:border-[#2d353b] text-[#475569] dark:text-[#94a3b8]">
            <Hourglass className="w-5 h-5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
              Rate limit reached
            </span>
            <p className="text-[13px] sm:text-[14px] text-[#475569] dark:text-[#94a3b8] truncate">
              Too many requests. Please wait a minute.
            </p>
          </div>
        </div>
        <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8] font-medium px-2.5 py-1 rounded-md bg-[#F1F5F9] dark:bg-[#22282c] shrink-0">
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
        className="w-full rounded-2xl p-4 sm:p-5 shadow-xs flex items-center justify-between gap-3 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in"
      >
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-[#B45309] dark:text-[#fcd34d] shrink-0" />
          <span className="text-[14px] text-[#0F172A] dark:text-[#f1f5f9]">
            Couldn&apos;t answer in time. Please try again.
          </span>
        </div>
        <button
          onClick={() => lastQuestion && sendUserMessage(lastQuestion)}
          disabled={isSending || !lastQuestion}
          className="min-h-[44px] px-3.5 py-1.5 rounded-xl text-[13px] font-semibold border flex items-center gap-1.5 transition-colors cursor-pointer bg-[#F8FAFC] border-[#E2E8F0] hover:bg-[#F1F5F9] text-[#0F172A] dark:bg-[#2d353b] dark:border-[#2d353b] dark:text-[#f1f5f9] dark:hover:bg-[#2d353b]"
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
      <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in">
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-[#F1F5F9] border-[#E2E8F0] text-[#475569] dark:bg-[#22282c] dark:border-[#2d353b] dark:text-[#94a3b8]">
            <Info className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-1 min-w-0">
            <span className="text-[16px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
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
                className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#0D9488] dark:text-[#6ee7b7] hover:underline min-h-[44px]"
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
    const choices = message.options?.length
      ? message.options
      : (meta?.schemes || []).slice(0, 5).map((s) => ({
          id: s.id,
          label: shortSchemeName(s.name),
          prompt: `Show facts for ${s.name}`,
        }));
    return (
      <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in">
        <div className="flex items-center gap-2.5">
          <SlidersHorizontal className="w-5 h-5 text-[#0D9488] dark:text-[#6ee7b7]" />
          <span className="text-[15px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
            Which scheme did you mean? Please select one to view its facts:
          </span>
        </div>
        <div className="flex flex-col gap-2 pt-1">
          {choices.map((c) => {
            const house = meta?.schemes.find((s) => s.id === c.id)?.amc_name;
            const facts = schemeFacts.find((f) => f.scheme_id === c.id);
            const nav = facts?.nav?.value;
            const aum = facts?.aum?.value;
            return (
              <button
                key={c.id}
                onClick={() => sendUserMessage(c.prompt)}
                disabled={isSending}
                className="group w-full min-h-[56px] px-4 py-3 rounded-xl text-left border transition-colors cursor-pointer flex items-center gap-3 bg-[#F8FAFC] border-[#E2E8F0] hover:bg-teal-50 hover:border-[#0D9488] dark:bg-[#22282c] dark:border-[#2d353b] dark:hover:bg-[#2d353b] disabled:opacity-50"
                type="button"
              >
                <span className="flex-1 min-w-0 flex flex-col gap-0.5">
                  <span className="text-[14px] font-semibold text-[#0F172A] group-hover:text-[#0D9488] dark:text-[#f1f5f9] dark:group-hover:text-[#6ee7b7]">
                    {c.label}
                  </span>
                  {(house || aum) && (
                    <span className="text-[12px] text-[#64748B] dark:text-[#94a3b8]">
                      {[house, aum && `AUM ${groupIndian(aum)}`].filter(Boolean).join(' · ')}
                    </span>
                  )}
                </span>
                {nav && <span className="text-[13px] font-semibold num-tabular text-[#0F172A] dark:text-[#f1f5f9]">NAV {nav}</span>}
                <ChevronRight className="w-4 h-4 shrink-0 text-[#64748B] dark:text-[#94a3b8]" aria-hidden="true" />
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  // 7. Compound Card (Answer portion + Neutral note using backend text unchanged)
  if (message.type === 'compound' || (message.text.includes('Note:') && message.text.includes('Answer'))) {
    const parsed = parseAnswerText(message.text);
    return (
      <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-4 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in">
        {/* Fact Component */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-[#0D9488] dark:text-[#6ee7b7]" />
              <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
                Answer
              </span>
            </div>
            <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8]">{dataAsOf}</span>
          </div>

          <p className="text-[14px] sm:text-[15px] leading-relaxed text-[#0F172A] dark:text-[#f1f5f9]">
            {parsed.prose}
          </p>

          {/* Stat Matrix if available */}
          {parsed.metrics.length > 0 && (
            <div className="rounded-xl p-3.5 border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#22282c] dark:border-[#2d353b]">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {parsed.metrics.map((m, idx) => (
                  <div key={idx} className="flex flex-col">
                    <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8] mb-0.5">
                      {m.label}
                    </span>
                    <span className="text-[14px] font-semibold text-[#0F172A] dark:text-[#f1f5f9]">
                      {m.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="w-full h-px bg-[#E2E8F0] dark:bg-[#2d353b]" />

        {/* Neutral note portion using backend text unchanged */}
        <div className="flex items-start gap-2.5 p-3.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#22282c]/70 dark:border-[#2d353b]">
          <Info className="w-4 h-4 text-[#64748B] dark:text-[#94a3b8] shrink-0 mt-0.5" />
          <p className="text-[13px] sm:text-[14px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
            <strong className="text-[#0F172A] dark:text-[#f1f5f9]">Note:</strong>{' '}
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
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[13px] font-semibold transition-colors min-h-[44px] bg-[#F8FAFC] border-[#E2E8F0] text-[#0D9488] hover:bg-teal-50 dark:bg-[#22282c] dark:border-[#2d353b] dark:text-[#6ee7b7] dark:hover:bg-[#2d353b]"
          >
            <LinkIcon className="w-3.5 h-3.5" />
            <span>{sourceLabel}</span>
          </a>
          <button
            onClick={() => handleCopy(parsed.prose)}
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#f1f5f9] min-h-[44px] px-2 cursor-pointer"
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
    isNoInfoAnswer ||
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

    const info = parseAnswerText(message.text);
    return (
      <div className="w-full rounded-2xl p-5 shadow-sm flex items-start gap-3.5 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-[#F8FAFC] border-[#E2E8F0] text-[#475569] dark:bg-[#22282c] dark:border-[#2d353b] dark:text-[#94a3b8]">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div className="flex flex-col gap-2 min-w-0">
          <span className="text-[15px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
            {title}
          </span>
          <p className="text-[14px] leading-relaxed whitespace-pre-line text-[#475569] dark:text-[#94a3b8]">
            {info.prose || message.text || 'I can only answer factual questions about these schemes.'}
          </p>
          {info.metrics.length > 0 && (
            <dl className="grid grid-cols-1 gap-2.5 rounded-xl p-3.5 border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#22282c] dark:border-[#2d353b]">
              {info.metrics.map((m, idx) => (
                <div key={idx} className="flex flex-col">
                  <dt className="text-[13px] text-[#64748B] dark:text-[#94a3b8]">{m.label}</dt>
                  <dd className="text-[14px] font-semibold text-[#0F172A] dark:text-[#f1f5f9] leading-snug">{m.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </div>
    );
  }

  // 9. Standard Answer Card (fact_store / llm_synthesis / answer)
  const parsed = parseAnswerText(message.text);

  return (
    <div className="w-full rounded-2xl p-5 shadow-sm flex flex-col gap-4 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b] animate-fade-in">
      {/* Top Bar: Check icon badge + "Answer" + "Data as of <as_of>" */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md flex items-center justify-center font-bold bg-emerald-100 text-[#0D9488] dark:bg-[#6ee7b7] dark:text-[#132e27]">
            <Check className="w-4 h-4 stroke-[3]" />
          </div>
          <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
            Answer
          </span>
        </div>
        <span className="text-[13px] font-medium text-[#64748B] dark:text-[#94a3b8]">{dataAsOf}</span>
      </div>

      {/* Narrative Prose */}
      <div className="text-[14px] sm:text-[15px] leading-relaxed text-[#0F172A] dark:text-[#f1f5f9]">
        <p className="whitespace-pre-wrap">{parsed.prose || message.text}</p>
      </div>

      {/* Stat Matrix (Grid with no cell truncation) */}
      {parsed.metrics.length > 0 && (
        <div className="rounded-xl p-4 border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#22282c] dark:border-[#2d353b]">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
            {parsed.metrics.map((m, idx) => (
              <div key={idx} className="flex flex-col">
                <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8] mb-0.5">
                  {m.label}
                </span>
                <span className="text-[14px] font-semibold text-[#0F172A] dark:text-[#f1f5f9] leading-snug">
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
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[13px] font-semibold transition-colors min-h-[44px] bg-[#F8FAFC] border-[#E2E8F0] text-[#0D9488] hover:bg-teal-50 dark:bg-[#22282c] dark:border-[#2d353b] dark:text-[#6ee7b7] dark:hover:bg-[#2d353b]"
        >
          <LinkIcon className="w-3.5 h-3.5" />
          <span>{sourceLabel}</span>
        </a>

        {/* Action Controls: Thumbs Up / Down / Copy / Report */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 p-0.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#22282c] dark:border-[#2d353b]">
            <button
              onClick={() => submitMessageFeedback(message.id, 'up')}
              className={`w-9 h-9 flex items-center justify-center rounded-lg transition-colors cursor-pointer ${
                message.userFeedback === 'up'
                  ? 'text-[#0D9488] bg-teal-50 dark:text-[#6ee7b7] dark:bg-[#2d353b]'
                  : 'text-[#64748B] hover:text-[#0D9488] dark:text-[#94a3b8] dark:hover:text-[#6ee7b7]'
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
                  ? 'text-red-500 bg-red-50 dark:text-red-400 dark:bg-[#2d353b]'
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
              className="w-9 h-9 flex items-center justify-center rounded-lg text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#f1f5f9] transition-colors cursor-pointer"
              title="Copy to clipboard"
              type="button"
              aria-label="Copy answer"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => submitMessageFeedback(message.id, 'reported')}
            className="text-[13px] text-[#64748B] hover:text-[#92400E] dark:text-[#94a3b8] dark:hover:text-[#fcd34d] underline decoration-dotted min-h-[44px] cursor-pointer"
            type="button"
          >
            {message.userFeedback === 'reported' ? 'Report submitted' : 'Report incorrect answer'}
          </button>
        </div>
      </div>
    </div>
  );
};
