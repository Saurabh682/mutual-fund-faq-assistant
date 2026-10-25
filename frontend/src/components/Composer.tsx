import React, { useState } from 'react';
import { ArrowUp, ChevronDown, HelpCircle, ShieldAlert, Sparkles } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

const PII_WARNING_PATTERN =
  /\b([a-zA-Z]{5}\s*\d{4}\s*[a-zA-Z]|\d{4}[\s-]?\d{4}[\s-]?\d{4}|folio|otp|password|bank account|ifsc)\b/i;

const QUICK_SCHEMES = [
  'HDFC Mid-Cap Opportunities Fund',
  'HDFC Small Cap Fund',
  'HDFC Top 100 Fund',
  'HDFC Silver ETF FoF',
  'HDFC Multi Cap Fund',
];

const SUGGESTED_QUESTIONS = [
  { category: 'Exit Load & Lock-in', q: 'What is the exit load for HDFC Mid-Cap Opportunities Fund?' },
  { category: 'SIP & Limits', q: 'What is the minimum SIP amount for HDFC Small Cap Fund?' },
  { category: 'Expense Ratio (TER)', q: 'What is the expense ratio for HDFC Top 100 Fund (Direct - Growth)?' },
  { category: 'Fund Management', q: 'Who manages HDFC Silver ETF FoF?' },
  { category: 'Benchmark Index', q: 'What is the benchmark for HDFC Multi Cap Fund?' },
  { category: 'Groww Procedure', q: 'How do I download my Capital Gains statement on Groww?' },
];

export const Composer: React.FC = () => {
  const [text, setText] = useState('');
  const [showQuickSchemes, setShowQuickSchemes] = useState(false);
  const [showWhatCanIAsk, setShowWhatCanIAsk] = useState(false);
  const { sendUserMessage, isSending } = useChatStore();

  const hasPiiWarning = PII_WARNING_PATTERN.test(text);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim() || isSending) return;
    sendUserMessage(text);
    setText('');
    setShowQuickSchemes(false);
    setShowWhatCanIAsk(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelectScheme = (schemeName: string) => {
    setText(`What is the expense ratio and exit load for ${schemeName}?`);
    setShowQuickSchemes(false);
  };

  const handleSelectSuggestedQuestion = (question: string) => {
    setText(question);
    setShowWhatCanIAsk(false);
  };

  return (
    <div className="shrink-0 bg-[#12161A] border-t border-[#28323E] p-4 md:px-8 z-20">
      <div className="max-w-[860px] mx-auto flex flex-col gap-2">
        {/* Soft Client PII Warning */}
        {hasPiiWarning && (
          <div className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2 text-xs text-amber-300 animate-fadeIn">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>
              DPDP Guardrail Notice: Please do not submit real PAN, Aadhaar, folio, or bank OTP credentials.
            </span>
          </div>
        )}

        {/* Guardrail Notice Pill above input */}
        <div className="flex items-center justify-between px-1 text-[11px]">
          <div className="flex items-center gap-1.5 text-slate-400">
            <span className="flex items-center justify-center w-4 h-4 rounded-full bg-slate-800 text-slate-300 text-[10px]">
              🔒
            </span>
            <span className="font-medium text-slate-300">DPDP Shield Active:</span>
            <span className="text-slate-500 hidden sm:inline">
              Never share PAN, Aadhaar, folio number, or bank OTPs.
            </span>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
            <span className="hidden sm:inline">Tokens: 1.2k cached</span>
            <span className="hidden sm:inline">•</span>
            <span className="text-emerald-400 font-semibold">Latency: &lt; 50ms (Fact Store)</span>
          </div>
        </div>

        {/* Input Container: Rounded 16px slate box with 1px border */}
        <div className="bg-[#1A2027] border border-[#28323E] focus-within:border-[#00D09C] focus-within:ring-1 focus-within:ring-[#00D09C]/40 rounded-2xl p-2.5 transition shadow-lg relative">
          <textarea
            rows={2}
            value={text}
            onChange={(e) => setText(e.target.value.slice(0, 500))}
            onKeyDown={handleKeyDown}
            placeholder="Ask a factual question about HDFC schemes (e.g. TER, exit load, SIP limit, fund manager)..."
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 resize-none focus:outline-none px-2 py-1"
          />

          <div className="flex items-center justify-between pt-2 border-t border-[#28323E]/50 px-1 mt-1">
            {/* Left Controls / Quick Scheme Selector Pill & What Can I Ask */}
            <div className="relative flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowQuickSchemes(!showQuickSchemes);
                  setShowWhatCanIAsk(false);
                }}
                className="flex items-center gap-1.5 text-[11px] bg-[#12161A] hover:bg-[#202832] text-slate-300 hover:text-white px-2.5 py-1 rounded-lg border border-[#28323E] transition cursor-pointer"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#00D09C]"></span>
                <span className="font-medium">Quick Schemes</span>
                <ChevronDown className="w-3 h-3 text-slate-400" />
              </button>

              <button
                type="button"
                onClick={() => {
                  setShowWhatCanIAsk(!showWhatCanIAsk);
                  setShowQuickSchemes(false);
                }}
                className="flex items-center gap-1.5 text-[11px] bg-[#12161A] hover:bg-[#202832] text-slate-300 hover:text-[#00D09C] px-2.5 py-1 rounded-lg border border-[#28323E] hover:border-[#00D09C]/40 transition cursor-pointer"
                title="View what topics and questions you can ask"
              >
                <HelpCircle className="w-3.5 h-3.5 text-[#00D09C]" />
                <span className="font-medium">What can I ask?</span>
              </button>

              {showQuickSchemes && (
                <div className="absolute left-0 bottom-full mb-2 w-64 bg-[#151A20] border border-[#28323E] rounded-xl shadow-2xl p-2 z-50 flex flex-col gap-1 animate-fadeIn">
                  <div className="text-[10px] font-mono text-slate-400 px-2 py-1 uppercase tracking-wider">
                    Select HDFC Scheme
                  </div>
                  {QUICK_SCHEMES.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => handleSelectScheme(s)}
                      className="text-left text-xs text-slate-200 hover:text-white hover:bg-[#1A2027] px-2.5 py-1.5 rounded-lg transition truncate cursor-pointer"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {showWhatCanIAsk && (
                <div className="absolute left-0 bottom-full mb-2 w-80 sm:w-96 bg-[#151A20] border border-[#28323E] rounded-xl shadow-2xl p-3 z-50 flex flex-col gap-2.5 animate-fadeIn">
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#28323E]">
                    <div className="text-[11px] font-bold text-white flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-[#00D09C]" />
                      <span>What you can ask</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        sendUserMessage('What can I ask?');
                        setShowWhatCanIAsk(false);
                      }}
                      className="text-[10px] text-[#00D09C] hover:underline cursor-pointer"
                    >
                      Ask in chat →
                    </button>
                  </div>

                  <div className="flex flex-col gap-1.5 max-h-64 overflow-y-auto pr-1">
                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      Factual Topics (Click to ask)
                    </div>
                    {SUGGESTED_QUESTIONS.map((item) => (
                      <button
                        key={item.q}
                        type="button"
                        onClick={() => handleSelectSuggestedQuestion(item.q)}
                        className="text-left text-xs bg-[#1A2027] hover:bg-[#202832] hover:border-[#00D09C]/40 border border-transparent p-2 rounded-lg transition flex flex-col gap-0.5 cursor-pointer group"
                      >
                        <span className="text-[10px] font-semibold text-[#00D09C]">{item.category}</span>
                        <span className="text-slate-300 group-hover:text-white text-[11.5px] leading-snug">
                          "{item.q}"
                        </span>
                      </button>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-[#28323E]/80 text-[10px] text-slate-500 flex items-center justify-between">
                    <span>🛡️ 5 Official HDFC Schemes</span>
                    <span className="text-red-400/80">Zero advice or predictions</span>
                  </div>
                </div>
              )}

              <div className="hidden sm:flex items-center gap-1 text-[11px] text-slate-500 font-mono">
                <span>Scope:</span>
                <span className="text-slate-300">5 Schemes</span>
              </div>
            </div>

            {/* Right: Character counter & Circular Emerald Send Button */}
            <div className="flex items-center gap-3">
              <span className="text-[11px] font-mono text-slate-500 num-tabular">
                {text.length} / 500
              </span>

              <button
                type="button"
                onClick={() => handleSubmit()}
                disabled={!text.trim() || isSending}
                className="w-8 h-8 rounded-full bg-[#00D09C] hover:bg-[#00B386] active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed text-[#12161A] flex items-center justify-center font-bold transition shadow-md shadow-[#00D09C]/25 cursor-pointer"
                title="Send question"
              >
                <ArrowUp className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Micro-footer */}
        <div className="flex items-center justify-center text-[10px] text-slate-600 gap-2">
          <span>Powered by Groww Scheme Facts API</span>
          <span>•</span>
          <span>AMFI Registered</span>
          <span>•</span>
          <span>SEBI Regulations Compliant</span>
        </div>
      </div>
    </div>
  );
};
