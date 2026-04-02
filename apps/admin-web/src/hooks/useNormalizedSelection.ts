import { useEffect } from "react";

export function useNormalizedSelection<T>(
  items: T[],
  selectedId: string | null,
  getId: (item: T) => string,
  onChange: (nextId: string | null) => void,
) {
  useEffect(() => {
    const nextSelectedId = items.some((item) => getId(item) === selectedId)
      ? selectedId
      : (items[0] ? getId(items[0]) : null);

    if (nextSelectedId !== selectedId) {
      onChange(nextSelectedId);
    }
  }, [getId, items, onChange, selectedId]);
}
