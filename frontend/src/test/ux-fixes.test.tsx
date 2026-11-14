import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import React from 'react';
import { AboutModal } from '../components/AboutModal';
import { FactSheetContent } from '../components/FactSheetDrawer';
import { Header } from '../components/Header';
import { MessageBubble } from '../components/MessageBubble';
import { MessageFeed } from '../components/MessageFeed';
import { ThreadSidebar } from '../components/ThreadSidebar';
import { parseAnswerText } from '../lib/answerText';
import { formatDate, groupIndian, plainExitLoad } from '../lib/format';
import { useChatStore } from '../store/useChatStore';
import type { Message, SchemeFacts, Thread } from '../types/chat';

const FACTS: SchemeFacts = {
  scheme_id: 'hdfc_midcap_dg',
  scheme_name: 'HDFC Mid-Cap Opportunities Fund (Direct - Growth)',
  ter_direct: { value: '0.73%', as_of: '2026-11-13' },
  exit_load: { value: 'Exit load of 1% if redeemed within 1 year.', as_of: '2026-11-13' },
  min_sip: { value: '₹100', as_of: '2026-11-13' },
  min_lumpsum: { value: '₹100', as_of: '2026-11-13' },
  lock_in: { value: 'None', as_of: '2026-11-13' },
  riskometer: { value: 'Very High', as_of: '2026-11-13' },
  benchmark: { value: 'NIFTY Midcap 150 Total Return Index', as_of: '2026-11-13' },
  fund_manager: { value: 'Chirag Setalvad', as_of: '2026-11-13' },
  nav: { value: '₹229.697', as_of: '2026-11-13' },
  aum: { value: '₹100687.07 Cr', as_of: '2026-11-13' },
};

const META = {
  amc: 'HDFC Mutual Fund',
  disclaimer: 'Facts-only. No investment advice.',
  starter_questions: ['What is the exit load for HDFC Mid-Cap Opportunities Fund?'],
  schemes: [
    { id: 'hdfc_midcap_dg', name: 'HDFC Mid-Cap Opportunities Fund (Direct - Growth)' },
    { id: 'hdfc_smallcap_dg', name: 'HDFC Small Cap Fund (Direct - Growth)' },
  ],
};

const msg = (over: Partial<Message>): Message => ({
  id: 'm1',
  role: 'assistant',
  type: 'fact_store',
  text: '',
  timestamp: new Date().toISOString(),
  ...over,
});

const thread = (messages: Message[]): Thread => ({
  id: 't1',
  client_id: 'c',
  title: 'New Conversation',
  created_at: '',
  updated_at: '',
  message_count: messages.length,
  messages,
});

beforeEach(() => {
  act(() => {
    useChatStore.setState({
      meta: META,
      schemeFacts: [FACTS],
      factsState: 'ready',
      selectedSchemeId: 'hdfc_midcap_dg',
      activeThread: null,
      activeThreadId: null,
      threads: [],
      isSending: false,
      isAboutModalOpen: false,
    });
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('formatting helpers', () => {
  it('formats dates without inventing one', () => {
    expect(formatDate('2026-11-13')).toBe('13 Nov 2026');
    expect(formatDate(undefined)).toBe('');
    expect(formatDate('')).toBe('');
  });

  it('groups numbers the Indian way and leaves grouped ones alone', () => {
    expect(groupIndian('₹100687.07 Cr')).toBe('₹1,00,687.07 Cr');
    expect(groupIndian('₹38512.3 Cr')).toBe('₹38,512.3 Cr');
    expect(groupIndian('₹101,856 Cr')).toBe('₹101,856 Cr');
    expect(groupIndian('₹229.697')).toBe('₹229.697');
    expect(groupIndian('0.73%')).toBe('0.73%');
  });

  it('drops the repeated "Exit load of" lead-in', () => {
    expect(plainExitLoad('Exit load of 1% if redeemed within 1 year.')).toBe('1% if redeemed within 1 year.');
    expect(plainExitLoad('Nil')).toBe('Nil');
  });

  it('parses a table without its header row, the AMFI code or the fund house', () => {
    const parsed = parseAnswerText(
      'Intro sentence.\n\n| Aspect | Detail |\n| :--- | :--- |\n| **Financial Term** | TER |\n| **AMFI Code** | 130503 |\n| **Fund House** | HDFC |'
    );
    expect(parsed.prose).toBe('Intro sentence.');
    expect(parsed.metrics).toEqual([{ label: 'Financial Term', value: 'TER' }]);
  });
});

describe('answer cards', () => {
  it('renders a glossary table as a list, not as raw markup', () => {
    render(
      <MessageBubble
        message={msg({
          type: 'glossary',
          text: 'Total Expense Ratio (TER) covers annual costs.\n\n| Aspect | Detail |\n| :--- | :--- |\n| **Financial Term** | Total Expense Ratio (TER) |\n| **Definition** | Annual operating fee |',
        })}
      />
    );
    expect(screen.getByText('Glossary Definition')).toBeInTheDocument();
    expect(screen.getByText('Financial Term')).toBeInTheDocument();
    expect(screen.getByText('Annual operating fee')).toBeInTheDocument();
    expect(screen.queryByText(/:---/)).toBeNull();
    expect(screen.queryByText(/\*\*/)).toBeNull();
    expect(screen.queryByText('Aspect')).toBeNull();
  });

  it('shows a "no information" reply as not found, even when saved as a synthesized answer', () => {
    render(
      <MessageBubble
        message={msg({
          type: 'llm_synthesis',
          text: "I don't have that information. I can answer questions about TER, exit load and minimum SIP.",
          last_updated: '2026-11-13',
        })}
      />
    );
    expect(screen.getByText('Information not found')).toBeInTheDocument();
    expect(screen.queryByText('Answer')).toBeNull();
    expect(screen.queryByText(/Source: Groww scheme page/)).toBeNull();
  });

  it('leaves out the AMFI code and shows no date when the message has none', () => {
    render(
      <MessageBubble
        message={msg({
          text: 'The exit load for HDFC Small Cap Fund is 1% if redeemed within 1 year.\n\n| Metric | Value |\n| :--- | :--- |\n| **Scheme** | HDFC Small Cap Fund |\n| **Exit Load** | 1% if redeemed within 1 year |\n| **AMFI Code** | 130503 |',
        })}
      />
    );
    expect(screen.getByText('Exit Load')).toBeInTheDocument();
    expect(screen.queryByText('AMFI Code')).toBeNull();
    expect(screen.queryByText(/Data as of/)).toBeNull();
    expect(screen.getByText('Source: Groww scheme page')).toBeInTheDocument();
  });

  it('retries the real last question, not a placeholder', () => {
    const sendUserMessage = vi.fn();
    const question = msg({ id: 'u1', role: 'user', type: 'user_query', text: 'What is the TER of HDFC Top 100 Fund?' });
    const timedOut = msg({ id: 'a1', type: 'timeout', text: "Couldn't answer in time. Please try again." });
    act(() => {
      useChatStore.setState({ sendUserMessage, activeThread: thread([question, timedOut]) });
    });
    render(<MessageBubble message={timedOut} />);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(sendUserMessage).toHaveBeenCalledWith('What is the TER of HDFC Top 100 Fund?');
  });
});

describe('fact sheet', () => {
  it('formats the exit load and AUM, and states the date once', () => {
    render(<FactSheetContent />);
    expect(screen.getByText('1% if redeemed within 1 year.')).toBeInTheDocument();
    expect(screen.getByText('₹1,00,687.07 Cr')).toBeInTheDocument();
    expect(screen.queryAllByText(/^as of /)).toHaveLength(0);
    expect(screen.getByText('Source: Groww scheme page · Data as of 13 Nov 2026')).toBeInTheDocument();
  });

  it('flags a row whose date differs from the rest', () => {
    act(() => {
      useChatStore.setState({ schemeFacts: [{ ...FACTS, nav: { value: '₹229.697', as_of: '2026-10-01' } }] });
    });
    render(<FactSheetContent />);
    expect(screen.getAllByText('as of 1 Oct 2026')).toHaveLength(1);
    expect(screen.getByText('Source: Groww scheme page · Data as of 13 Nov 2026')).toBeInTheDocument();
  });

  it('shows a loading state instead of dashes and a made-up date', () => {
    act(() => {
      useChatStore.setState({ schemeFacts: [], factsState: 'loading' });
    });
    render(<FactSheetContent />);
    expect(screen.getByRole('status', { name: /loading fact sheet/i })).toBeInTheDocument();
    expect(screen.queryByText('—')).toBeNull();
    expect(screen.queryByText(/5 Nov 2026/)).toBeNull();
  });

  it('says so when the facts could not be loaded, and offers a retry', () => {
    const reloadSchemeFacts = vi.fn();
    act(() => {
      useChatStore.setState({ schemeFacts: [], factsState: 'error', reloadSchemeFacts });
    });
    render(<FactSheetContent />);
    expect(screen.getByRole('alert')).toHaveTextContent(/couldn't load this fact sheet/i);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(reloadSchemeFacts).toHaveBeenCalledTimes(1);
  });
});

describe('header', () => {
  it('shows the real data date, and no date while it is unknown', () => {
    const { unmount } = render(<Header />);
    expect(screen.getByText('Data as of 13 Nov 2026')).toBeInTheDocument();
    unmount();

    act(() => {
      useChatStore.setState({ meta: null, schemeFacts: [], factsState: 'loading' });
    });
    render(<Header />);
    expect(screen.queryByText(/Data as of/)).toBeNull();
    expect(screen.getByRole('combobox', { name: /select scheme/i })).toBeDisabled();
  });
});

describe('message feed', () => {
  it('does not scroll an empty chat to its bottom, but does once there are messages', () => {
    const scroll = vi.spyOn(window.HTMLElement.prototype, 'scrollIntoView');
    act(() => {
      useChatStore.setState({ activeThread: thread([]) });
    });
    const { rerender } = render(<MessageFeed />);
    expect(scroll).not.toHaveBeenCalled();

    act(() => {
      useChatStore.setState({ activeThread: thread([msg({ id: 'u1', role: 'user', type: 'user_query', text: 'hi' })]) });
    });
    rerender(<MessageFeed />);
    expect(scroll).toHaveBeenCalled();
  });

  it('announces a new answer to screen readers but not an already-open thread', () => {
    const question = msg({ id: 'u1', role: 'user', type: 'user_query', text: 'TER?' });
    act(() => {
      useChatStore.setState({ activeThread: thread([question]) });
    });
    render(<MessageFeed />);
    const live = screen.getAllByRole('status').find((el) => el.className.includes('sr-only'))!;
    expect(live).toHaveTextContent('');

    act(() => {
      useChatStore.setState({ activeThread: thread([question, msg({ id: 'a1', text: 'The TER of HDFC Small Cap Fund is 0.79%.' })]) });
    });
    expect(live).toHaveTextContent('The TER of HDFC Small Cap Fund is 0.79%.');
  });
});

describe('sidebar', () => {
  const summary = (id: string, title: string, count: number) => ({
    id,
    client_id: 'c',
    title,
    created_at: '',
    updated_at: '',
    message_count: count,
  });

  it('lists only chats with messages plus the open one', () => {
    act(() => {
      useChatStore.setState({
        threads: [summary('a', 'Old blank draft', 0), summary('b', 'TER of Small Cap', 2), summary('c', 'Current empty chat', 0)],
        activeThreadId: 'c',
        activeThread: thread([]),
      });
    });
    render(<ThreadSidebar />);
    const nav = screen.getByRole('navigation', { name: /conversation history/i });
    expect(within(nav).getByText('TER of Small Cap')).toBeInTheDocument();
    expect(within(nav).getByText('Current empty chat')).toBeInTheDocument();
    expect(within(nav).queryByText('Old blank draft')).toBeNull();
  });

  it('"New chat" on an empty chat reuses it instead of creating another', () => {
    const startNewThread = vi.fn();
    act(() => {
      useChatStore.setState({ startNewThread, activeThreadId: 't1', activeThread: thread([]), threads: [summary('t1', 'New Conversation', 0)] });
    });
    render(<ThreadSidebar />);
    fireEvent.click(screen.getByRole('button', { name: /new chat/i }));
    expect(startNewThread).not.toHaveBeenCalled();

    act(() => {
      useChatStore.setState({ activeThread: thread([msg({ id: 'u1', role: 'user', type: 'user_query', text: 'hi' })]) });
    });
    fireEvent.click(screen.getByRole('button', { name: /new chat/i }));
    expect(startNewThread).toHaveBeenCalledTimes(1);
  });
});

describe('dialogs', () => {
  it('names the about dialog, moves focus into it and closes on Escape', () => {
    // jsdom has no layout, so say that every element is shown
    vi.spyOn(Element.prototype, 'getClientRects').mockReturnValue([{}] as unknown as DOMRectList);
    act(() => {
      useChatStore.setState({ isAboutModalOpen: true });
    });
    render(<AboutModal />);
    expect(screen.getByRole('dialog', { name: 'About FundFacts' })).toBeInTheDocument();
    expect(document.activeElement).toBe(screen.getByRole('button', { name: /close details modal/i }));
    expect(screen.getByText(/Covers 2 HDFC Direct-Growth schemes/)).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(useChatStore.getState().isAboutModalOpen).toBe(false);
  });
});
