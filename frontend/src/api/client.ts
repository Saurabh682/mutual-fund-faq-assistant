import type { Message, MetaData, SchemeFacts, Thread, ThreadSummary } from '../types/chat';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');

export async function fetchMetadata(): Promise<MetaData> {
  const res = await fetch(`${API_BASE}/meta`);
  if (!res.ok) throw new Error(`Failed to fetch metadata: ${res.statusText}`);
  return res.json();
}

export async function fetchSchemeFacts(): Promise<{ schemes: SchemeFacts[] }> {
  const res = await fetch(`${API_BASE}/facts/schemes`);
  if (!res.ok) throw new Error(`Failed to fetch scheme facts: ${res.statusText}`);
  return res.json();
}

export async function fetchThreads(clientId: string): Promise<ThreadSummary[]> {
  const res = await fetch(`${API_BASE}/threads?client_id=${encodeURIComponent(clientId)}`, {
    headers: { 'X-Client-Id': clientId },
  });
  if (!res.ok) throw new Error(`Failed to fetch threads: ${res.statusText}`);
  return res.json();
}

export async function fetchThread(threadId: string): Promise<Thread> {
  const res = await fetch(`${API_BASE}/threads/${threadId}`);
  if (!res.ok) throw new Error(`Failed to fetch thread ${threadId}: ${res.statusText}`);
  return res.json();
}

export async function createThread(clientId: string, title?: string): Promise<Thread> {
  const res = await fetch(`${API_BASE}/threads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Id': clientId,
    },
    body: JSON.stringify({ client_id: clientId, title: title || 'New Conversation' }),
  });
  if (!res.ok) throw new Error(`Failed to create thread: ${res.statusText}`);
  return res.json();
}

export async function deleteThread(threadId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/threads/${threadId}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 404) {
    throw new Error(`Failed to delete thread: ${res.statusText}`);
  }
}

export async function sendMessage(
  threadId: string,
  text: string,
  clientId: string
): Promise<Message> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s client timeout

  try {
    const res = await fetch(`${API_BASE}/threads/${threadId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Id': clientId,
      },
      body: JSON.stringify({ text }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.status === 429) {
      return {
        id: `rate_${Date.now()}`,
        role: 'assistant',
        type: 'rate_limit',
        text: 'Too many requests. Please wait a minute before querying again.',
        timestamp: new Date().toISOString(),
      };
    }

    if (res.status === 400) {
      let errDetail = '';
      try {
        const errJson = await res.json();
        errDetail = JSON.stringify(errJson).toLowerCase();
      } catch {
        // ignore
      }
      if (errDetail.includes('pii') || errDetail.includes('pan') || errDetail.includes('aadhaar')) {
        return {
          id: `pii_${Date.now()}`,
          role: 'assistant',
          type: 'pii_warning',
          text: "Please don't share PAN, Aadhaar, folio numbers or OTPs. Your message was not processed.",
          timestamp: new Date().toISOString(),
        };
      }
    }

    if (!res.ok) {
      let errMsg = res.statusText;
      try {
        const errBody = await res.json();
        errMsg = errBody.detail || errBody.message || errMsg;
      } catch {
        // ignore
      }
      throw new Error(`Failed to send message: ${errMsg || `Status ${res.status}`}`);
    }

    return res.json();
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === 'AbortError') {
      return {
        id: `timeout_${Date.now()}`,
        role: 'assistant',
        type: 'timeout',
        text: "Couldn't answer in time. Please try again.",
        timestamp: new Date().toISOString(),
      };
    }
    throw err;
  }
}

export async function submitFeedback(payload: {
  message_id: string;
  rating: string;
  comment?: string;
}): Promise<void> {
  try {
    await fetch(`${API_BASE}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch {
    // Non-blocking telemetry
  }
}
