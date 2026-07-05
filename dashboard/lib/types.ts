// Mirrors shared/models.py Signal envelope. Keep in sync by hand for now.
export type Pillar = "production" | "code" | "ai_quality";
export type Status = "ok" | "warning" | "critical";

export interface Signal {
  pillar: Pillar;
  status: Status;
  headline: string;
  detail: Record<string, unknown>;
  ts: string; // ISO 8601
  id?: string; // optional — storage wraps Signals with an id; raw envelope has none
}

export interface EvalPoint {
  ts: string;
  hallucination: number; // 0..1
  drift: number; // 0..1
  threshold: number; // 0..1
}

// Matches dashboard_api /correlation response shape.
export interface CorrelationResponse {
  production: {
    title?: string;
    service?: string;
    suspect_commit?: string;
    summary?: string;
    next_action?: string;
    severity?: string;
  } | null;
  code: {
    mr_id?: number;
    commit?: string;
    findings?: Array<{
      severity: string;
      file?: string;
      message?: string;
      category?: string;
    }>;
  } | null;
  verdict: string | null;
}

// Eval-trend rows shaped by storage.eval_trends.recent().
export interface QualityTrendRow {
  suite?: string;
  hallucination_rate?: number;
  drift?: number;
  threshold?: number;
  passed?: boolean;
  ts?: string;
}
