interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  detail?: string;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const payload = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !payload.success) {
    throw new Error(payload.detail || `请求失败: ${path}`);
  }
  return payload.data;
}
