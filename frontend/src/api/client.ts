import type { Message, MetaData, Thread, ThreadSummary } from '../types/chat';

const API_BASE = '/api/v1';

export async function fetchMetadata(): Promise<MetaData> {
  const res = await fetch(`${API_BASE}/meta`);
  if (!res.ok) throw new Error(`Failed to fetch metadata: ${res.statusText}`);
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
  const res = await fetch(`${API_BASE}/threads/${threadId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Id': clientId,
    },
    body: JSON.stringify({ text }),
  });

  if (!res.ok && res.status !== 400) {
    throw new Error(`Failed to send message: ${res.statusText}`);
  }
  return res.json();
}
