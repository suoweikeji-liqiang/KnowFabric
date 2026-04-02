import { Dispatch, SetStateAction, useCallback, useEffect, useState } from "react";

function readStoredState<T>(storageKey: string, defaults: T): T {
  if (typeof window === "undefined") {
    return defaults;
  }

  const raw = window.localStorage.getItem(storageKey);
  if (!raw) {
    return defaults;
  }

  try {
    return { ...defaults, ...JSON.parse(raw) } as T;
  } catch {
    return defaults;
  }
}

export function usePersistentPageState<T extends Record<string, unknown>>(
  storageKey: string,
  defaults: T,
): [T, Dispatch<SetStateAction<T>>, (patch: Partial<T>) => void] {
  const [state, setState] = useState<T>(() => readStoredState(storageKey, defaults));

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    window.localStorage.setItem(storageKey, JSON.stringify(state));
  }, [storageKey, state]);

  const patchState = useCallback((patch: Partial<T>) => {
    setState((current) => ({ ...current, ...patch }));
  }, []);

  return [state, setState, patchState];
}
