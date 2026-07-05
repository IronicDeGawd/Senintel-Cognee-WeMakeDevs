// API base — set NEXT_PUBLIC_API_BASE at build time (Vercel env).
// Empty in dev = SWR falls back to mocked data so the UI still renders.

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ?? "";

export class ApiUnconfiguredError extends Error {
  constructor() {
    super("NEXT_PUBLIC_API_BASE not set");
    this.name = "ApiUnconfiguredError";
  }
}

export async function fetcher<T>(path: string): Promise<T> {
  if (!API_BASE) throw new ApiUnconfiguredError();
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} -> ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function postTrigger(
  pillar: "production" | "code" | "ai_quality",
): Promise<{ pillar: string; target: string; upstream_status: number }> {
  if (!API_BASE) throw new ApiUnconfiguredError();
  const res = await fetch(`${API_BASE}/trigger/${pillar}`, {
    method: "POST",
    cache: "no-store",
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (body as { detail?: string }).detail ?? `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return body;
}

export interface DemoRunResponse {
  upstream_status: number;
  result: {
    scenario?: string;
    ok?: boolean;
    steps?: Record<string, unknown>;
  };
}

export async function postDemoScenario(): Promise<DemoRunResponse> {
  if (!API_BASE) throw new ApiUnconfiguredError();
  const res = await fetch(`${API_BASE}/demo/run`, {
    method: "POST",
    cache: "no-store",
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (body as { detail?: string }).detail ?? `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return body as DemoRunResponse;
}
