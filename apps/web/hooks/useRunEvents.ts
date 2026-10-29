'use client';

import { useEffect, useRef, useState } from 'react';

export interface RunEvent {
  type: string;
  run_id: string;
  data: Record<string, unknown>;
  timestamp: string;
}

/**
 * Connects to the SSE endpoint for a given run ID and invokes `onEvent`
 * for every non-heartbeat event received. Safely no-ops if runId is empty.
 */
export function useRunEvents(runId: string, onEvent: (event: RunEvent) => void) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!runId || typeof window === 'undefined') {
      setConnected(false);
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const es = new EventSource(`${apiUrl}/api/runs/${runId}/events`);
      eventSourceRef.current = es;

      es.onopen = () => setConnected(true);
      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as RunEvent;
          if (data.type !== 'heartbeat') {
            onEvent(data);
          }
        } catch (e) {
          console.error('SSE parse error', e);
        }
      };
      es.onerror = () => {
        setConnected(false);
        es.close();
      };

      return () => {
        es.close();
        setConnected(false);
      };
    } catch {
      setConnected(false);
    }
  }, [runId, onEvent]);

  return { connected };
}
