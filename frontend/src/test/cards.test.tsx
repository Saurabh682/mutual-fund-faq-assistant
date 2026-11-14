import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import React from 'react';
import axe from 'axe-core';
import { MessageBubble } from '../components/MessageBubble';
import { FactSheetContent } from '../components/FactSheetDrawer';
import { StaleBanner } from '../components/StaleBanner';
import { useChatStore } from '../store/useChatStore';
import type { Message, SchemeFacts } from '../types/chat';

const MOCK_SCHEME_FACTS: SchemeFacts[] = [
  {
    scheme_id: 'hdfc_midcap_dg',
    scheme_name: 'HDFC Mid-Cap Opportunities Fund (Direct - Growth)',
    as_of: '2026-11-05',
    ter_direct: { value: '0.74%', as_of: '2026-11-05' },
    exit_load: { value: '1.00% if redeemed within 1 year', as_of: '2026-11-05' },
    min_sip: { value: '₹100', as_of: '2026-11-05' },
    min_lumpsum: { value: '₹100', as_of: '2026-11-05' },
    lock_in: { value: 'None', as_of: '2026-11-05' },
    riskometer: { value: 'Very High Risk', as_of: '2026-11-05' },
    benchmark: { value: 'NIFTY Midcap 150 TRI', as_of: '2026-11-05' },
    fund_manager: { value: 'Chirag Setalvad', as_of: '2026-11-05' },
    nav: { value: '₹226.14', as_of: '2026-11-05' },
    aum: { value: '₹101,856 Cr', as_of: '2026-11-05' },
  },
];

describe('UI Card Types and Component Unit Tests', () => {
  beforeEach(() => {
    act(() => {
      useChatStore.setState({
        schemeFacts: MOCK_SCHEME_FACTS,
        selectedSchemeId: 'hdfc_midcap_dg',
        meta: {
          amc: 'HDFC Mutual Fund',
          disclaimer: 'Facts-only. No investment advice.',
          starter_questions: [
            'What is the exit load for HDFC Mid-Cap Opportunities Fund?',
            'What is the minimum SIP amount for HDFC Small Cap Fund?',
            'What is the lock-in period for ELSS mutual funds?',
          ],
          schemes: [
            { id: 'hdfc_midcap_dg', name: 'HDFC Mid-Cap Opportunities Fund' },
            { id: 'hdfc_smallcap_dg', name: 'HDFC Small Cap Fund' },
          ],
        },
      });
    });
  });

  it('1. Renders Answer Card with check icon, date, text, stat matrix and action footer', async () => {
    const answerMsg: Message = {
      id: 'msg_answer_1',
      role: 'assistant',
      type: 'fact_store',
      text: `For HDFC Mid-Cap Opportunities Fund, the Total Expense Ratio (TER) is 0.74% and exit load is 1.00% within 1 year.

| Metric | Value |
| :--- | :--- |
| **Scheme** | HDFC Mid-Cap Opportunities Fund |
| **TER (Direct)** | 0.74% |
| **Exit Load** | 1.00% if redeemed <= 365 days |`,
      citation_url: 'https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth',
      last_updated: '2026-11-05',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={answerMsg} />);

    expect(screen.getByText('Answer')).toBeInTheDocument();
    expect(screen.getAllByText(/Data as of 5 Nov 2026/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Total Expense Ratio/i)).toBeInTheDocument();
    // Stat matrix parsed metrics
    expect(screen.getByText('TER (Direct)')).toBeInTheDocument();
    expect(screen.getByText('0.74%')).toBeInTheDocument();
    // Action footer
    expect(screen.getByText(/Source: Groww scheme page · Data as of 5 Nov 2026/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /mark helpful/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /mark unhelpful/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /copy answer/i })).toBeInTheDocument();
    expect(screen.getByText(/Report incorrect answer/i)).toBeInTheDocument();

    // WCAG validation
    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('2. Renders Refusal Card with "Can\'t help with that" and AMFI education link', async () => {
    const refusalMsg: Message = {
      id: 'msg_refusal_1',
      role: 'assistant',
      type: 'refusal',
      text: 'I can only provide objective facts about these schemes. I cannot recommend funds, compare them, or predict returns.',
      last_updated: '2026-11-05',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={refusalMsg} />);

    expect(screen.getByText("Can't help with that")).toBeInTheDocument();
    expect(screen.getByText(/I cannot recommend funds, compare them/i)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Learn more at AMFI investor education/i });
    expect(link).toHaveAttribute('href', 'https://www.amfiindia.com/investor-corner');

    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('3. Renders Compound Card with factual portion and neutral note portion', async () => {
    const compoundMsg: Message = {
      id: 'msg_compound_1',
      role: 'assistant',
      type: 'compound',
      text: `The minimum monthly SIP investment for HDFC Small Cap Fund (Direct Growth) is ₹100.
Note: I can only provide objective facts about these schemes. I cannot evaluate market timing or recommend whether to invest now.`,
      citation_url: 'https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth',
      last_updated: '2026-11-05',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={compoundMsg} />);

    expect(screen.getByText('Answer')).toBeInTheDocument();
    expect(screen.getByText(/The minimum monthly SIP investment/i)).toBeInTheDocument();
    expect(screen.getByText('Note:')).toBeInTheDocument();
    expect(screen.getByText(/I cannot evaluate market timing or recommend whether to invest now/i)).toBeInTheDocument();
    expect(screen.getByText(/Copy fact/i)).toBeInTheDocument();

    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('4. Renders Privacy & Security Warning card for PII block', async () => {
    const piiMsg: Message = {
      id: 'msg_pii_1',
      role: 'assistant',
      type: 'pii_warning',
      text: "Please don't share PAN, Aadhaar, folio numbers or OTPs. Your message was not processed.",
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={piiMsg} />);

    expect(screen.getByText('Privacy & Security Warning')).toBeInTheDocument();
    expect(screen.getByText(/Please don't share PAN, Aadhaar, folio numbers or OTPs/i)).toBeInTheDocument();

    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('5. Renders Rate-Limit Card for HTTP 429', async () => {
    const rateLimitMsg: Message = {
      id: 'msg_rate_1',
      role: 'assistant',
      type: 'rate_limit',
      text: 'Too many requests. Please wait a minute.',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={rateLimitMsg} />);

    expect(screen.getByText('Rate limit reached')).toBeInTheDocument();
    expect(screen.getByText(/Too many requests. Please wait a minute./i)).toBeInTheDocument();
    expect(screen.getByText('Wait ~45s')).toBeInTheDocument();

    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('6. Renders Timeout Error Card with retry button', async () => {
    const timeoutMsg: Message = {
      id: 'msg_timeout_1',
      role: 'assistant',
      type: 'timeout',
      text: "Couldn't answer in time. Please try again.",
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={timeoutMsg} />);

    expect(screen.getByText("Couldn't answer in time. Please try again.")).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();

    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('7. Renders Clarification Card with scheme buttons', async () => {
    const clarMsg: Message = {
      id: 'msg_clar_1',
      role: 'assistant',
      type: 'clarification',
      text: 'Which scheme did you mean? Please select one to view its facts:',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={clarMsg} />);

    expect(screen.getByText(/Which scheme did you mean/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /HDFC Mid-Cap Opportunities/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /HDFC Small Cap/i })).toBeInTheDocument();

    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('8. Renders Information not found card for not_found resolution', async () => {
    const notFoundMsg: Message = {
      id: 'msg_nf_1',
      role: 'assistant',
      type: 'not_found',
      text: "I don't have that information. I can answer questions about TER, exit load, minimum SIP, NAV, AUM, benchmark, riskometer, lock-in and fund manager for 5 HDFC schemes.",
      citation_url: 'https://groww.in',
      last_updated: '2026-11-05',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={notFoundMsg} />);
    expect(screen.getByText('Information not found')).toBeInTheDocument();
    expect(screen.getByText(/I don't have that information/i)).toBeInTheDocument();
    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('9. Renders Out of scope card for out_of_scope resolution', async () => {
    const oosMsg: Message = {
      id: 'msg_oos_1',
      role: 'assistant',
      type: 'out_of_scope',
      text: 'This assistant supports scheme facts for 5 HDFC schemes. For corporate AMC information, please refer to regulatory filings.',
      last_updated: '2026-11-05',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={oosMsg} />);
    expect(screen.getByText('Out of scope query')).toBeInTheDocument();
    expect(screen.getByText(/This assistant supports scheme facts for 5 HDFC schemes/i)).toBeInTheDocument();
    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('10. Renders Direct Plan Scope card for unsupported_plan resolution', async () => {
    const planMsg: Message = {
      id: 'msg_plan_1',
      role: 'assistant',
      type: 'unsupported_plan',
      text: 'This assistant only provides information for Direct - Growth plans of the supported HDFC schemes.',
      last_updated: '2026-11-05',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={planMsg} />);
    expect(screen.getByText('Direct Plan Scope')).toBeInTheDocument();
    expect(screen.getByText(/Direct - Growth plans/i)).toBeInTheDocument();
    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('11. Renders FactSheetContent with exactly 10 statutory rows and 6-segment Riskometer', async () => {
    const { container } = render(<FactSheetContent />);

    // Row 1: TER (Direct)
    expect(screen.getByText('TER (Direct)')).toBeInTheDocument();
    expect(screen.getByText('0.74%')).toBeInTheDocument();

    // Row 2: Exit load
    expect(screen.getByText('Exit load')).toBeInTheDocument();
    expect(screen.getByText('1.00% if redeemed within 1 year')).toBeInTheDocument();

    // Row 3: Minimum SIP
    expect(screen.getByText('Minimum SIP')).toBeInTheDocument();

    // Row 4: Minimum lumpsum
    expect(screen.getByText('Minimum lumpsum')).toBeInTheDocument();

    // Row 5: Lock-in
    expect(screen.getByText('Lock-in')).toBeInTheDocument();
    expect(screen.getByText('None')).toBeInTheDocument();

    // Row 6: Riskometer with 6-level segmented visual bar
    expect(screen.getByText('Riskometer')).toBeInTheDocument();
    expect(screen.getAllByText('Very High').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByLabelText(/Riskometer scale level 6 of 6/i)).toBeInTheDocument();

    // Row 7: Benchmark
    expect(screen.getByText('Benchmark')).toBeInTheDocument();
    expect(screen.getByText('NIFTY Midcap 150 TRI')).toBeInTheDocument();

    // Row 8: Fund manager (labeled: "Fund manager (as listed on source page)")
    expect(screen.getByText('Fund manager (as listed on source page)')).toBeInTheDocument();
    expect(screen.getByText('Chirag Setalvad')).toBeInTheDocument();

    // Row 9: NAV
    expect(screen.getByText('NAV')).toBeInTheDocument();
    expect(screen.getByText('₹226.14')).toBeInTheDocument();

    // Row 10: AUM
    expect(screen.getByText('AUM')).toBeInTheDocument();
    expect(screen.getByText('₹101,856 Cr')).toBeInTheDocument();

    // One date for the whole sheet (the footer); rows only repeat it when theirs differs
    expect(screen.queryAllByText(/^as of /i)).toHaveLength(0);

    // Footer
    expect(screen.getByText(/Source: Groww scheme page · Data as of 5 Nov 2026/i)).toBeInTheDocument();

    const results = await axe.run(container);
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  it('9. StaleBanner triggers only when as_of is older than 7 days', () => {
    // Test case A: Recent date (2 days ago) -> StaleBanner should NOT render
    const recentDate = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    act(() => {
      useChatStore.setState({
        schemeFacts: [
          {
            scheme_id: 'hdfc_midcap_dg',
            scheme_name: 'HDFC Mid-Cap Opportunities Fund',
            as_of: recentDate,
          },
        ],
        selectedSchemeId: 'hdfc_midcap_dg',
      });
    });

    const { rerender } = render(<StaleBanner />);
    expect(screen.queryByText(/Data is older than 7 days/i)).toBeNull();

    // Test case B: Stale date (20 days ago) -> StaleBanner should render
    const staleDate = new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    act(() => {
      useChatStore.setState({
        schemeFacts: [
          {
            scheme_id: 'hdfc_midcap_dg',
            scheme_name: 'HDFC Mid-Cap Opportunities Fund',
            as_of: staleDate,
          },
        ],
        selectedSchemeId: 'hdfc_midcap_dg',
      });
    });

    rerender(<StaleBanner />);
    expect(screen.getByText(/Data is older than 7 days/i)).toBeInTheDocument();
  });
});
