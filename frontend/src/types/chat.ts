export interface Message {
  id: string;
  role: 'user' | 'assistant';
  type:
    | 'user_query'
    | 'answer'
    | 'fact_store'
    | 'llm_synthesis'
    | 'refusal'
    | 'clarification'
    | 'not_found'
    | 'pii_block';
  text: string;
  sentence_count?: number;
  citation_url?: string;
  last_updated?: string;
  rendered?: string;
  timestamp: string;
  latency_ms?: number;
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
}

export interface MetaData {
  amc: string;
  disclaimer: string;
  starter_questions: string[];
  schemes: SchemeInfo[];
}
