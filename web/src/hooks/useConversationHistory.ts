import { useCallback, useState } from "react";

import type { AskResponse } from "../api/client";

const STORAGE_KEY = "vsa-conversation-history-v1";
const MAX_ITEMS = 20;

export interface HistoryItem {
  id: string;
  question: string;
  response: AskResponse;
  createdAt: string;
}

function loadHistory(): HistoryItem[] {
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]") as unknown;
    return Array.isArray(value) ? (value as HistoryItem[]).slice(0, MAX_ITEMS) : [];
  } catch {
    return [];
  }
}

export function useConversationHistory() {
  const [history, setHistory] = useState<HistoryItem[]>(loadHistory);

  const persist = useCallback((next: HistoryItem[]) => {
    setHistory(next);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }, []);

  const add = useCallback(
    (question: string, response: AskResponse) => {
      const next: HistoryItem[] = [
        {
          id: response.request_id ?? window.crypto.randomUUID(),
          question,
          response,
          createdAt: new Date().toISOString(),
        },
        ...history.filter((item) => item.id !== response.request_id),
      ].slice(0, MAX_ITEMS);
      persist(next);
    },
    [history, persist],
  );

  const clear = useCallback(() => persist([]), [persist]);

  return { history, add, clear };
}