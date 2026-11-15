export type MessageType =
  | 'user_query'
  | 'answer'
  | 'fact_store'
  | 'llm_synthesis'
  | 'refusal'
  | 'compound'
  | 'not_found'
  | 'out_of_scope'
  | 'unsupported_plan'
  | 'external_amc'
  | 'clarification'
  | 'pii_warning'
  | 'pii_block'
  | 'rate_limit'
  | 'timeout'
  | 'help'
  | 'glossary';

export interface StatMetric {
  label: string;
  value: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  type: MessageType;
  text: string;
  sentence_count?: number;
  citation_url?: string;
  last_updated?: string;
  rendered?: string;
  suggested_followups?: string[];
  /** Clarification choices: one per scheme the question may mean; prompt repeats the question */
  options?: { id: string; label: string; prompt: string }[];
  timestamp: string;
  latency_ms?: number;
  fact_portion?: string;
  note_portion?: string;
  metrics?: StatMetric[];
  userFeedback?: 'up' | 'down' | 'reported';
}

export interface ThreadSummary {
  id: string;
  client_id: string;
  title: string;
  last_scheme_id?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Thread extends ThreadSummary {
  messages: Message[];
}

export interface SchemeInfo {
  id: string;
  name: string;
  amc?: string;
  amc_name?: string;
  category?: string;
}

export interface MetaData {
  amc: string;
  disclaimer: string;
  starter_questions: string[];
  schemes: SchemeInfo[];
}

export interface FactMetric {
  value: string;
  as_of?: string;
  source_url?: string;
}

export interface SchemeFacts {
  scheme_id: string;
  scheme_name: string;
  as_of?: string;
  source_url?: string;
  ter_direct?: FactMetric;
  exit_load?: FactMetric;
  min_sip?: FactMetric;
  min_lumpsum?: FactMetric;
  lock_in?: FactMetric;
  riskometer?: FactMetric;
  benchmark?: FactMetric;
  fund_manager?: FactMetric;
  nav?: FactMetric;
  aum?: FactMetric;
  [key: string]: FactMetric | string | undefined;
}
