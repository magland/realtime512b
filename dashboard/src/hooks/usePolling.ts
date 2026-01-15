import { useEffect, useRef, useState } from 'react';

interface UsePollingOptions {
  interval: number; // milliseconds
  enabled?: boolean;
}

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  options: UsePollingOptions
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const intervalRef = useRef<number | null>(null);
  const { interval, enabled = true } = options;

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const fetchData = async () => {
      try {
        const result = await fetchFn();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Set up polling
    intervalRef.current = window.setInterval(fetchData, interval);

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchFn, interval, enabled]);

  return { data, error, isLoading };
}
