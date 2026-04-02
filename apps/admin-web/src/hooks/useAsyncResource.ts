import { useCallback, useEffect, useRef, useState } from "react";

interface AsyncResourceState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refresh: () => Promise<T | null>;
}

export function useAsyncResource<T>(
  loader: () => Promise<T>,
  deps: readonly unknown[],
): AsyncResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const loaderRef = useRef(loader);

  loaderRef.current = loader;

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await loaderRef.current();
      setData(next);
      return next;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      return null;
    } finally {
      setLoading(false);
    }
  }, [loader]);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const next = await loaderRef.current();
        if (!cancelled) {
          setData(next);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : String(caught));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, deps);

  return { data, error, loading, refresh };
}
