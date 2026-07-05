"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useQualityTrends } from "@/lib/hooks";

export function DriftChart() {
  const { data } = useQualityTrends(30);
  const rows = data ?? [];

  // API rows are newest-first; reverse so the chart reads left-to-right time.
  const series = [...rows].reverse().map((p, i) => ({
    i,
    hallucination: ((p.hallucination_rate ?? 0) * 100),
    drift: ((p.drift ?? 0) * 100),
    threshold: ((p.threshold ?? 0.1) * 100),
  }));

  const latest = rows[0];
  const hallPct = ((latest?.hallucination_rate ?? 0) * 100).toFixed(0);
  const driftPct = ((latest?.drift ?? 0) * 100).toFixed(0);
  const thrPct = ((latest?.threshold ?? 0.1) * 100).toFixed(0);

  const overThr = Number(hallPct) > Number(thrPct);

  return (
    <div className="flex h-full flex-col rounded-card-lg border border-line bg-bg-card p-7">
      <header className="flex items-end justify-between border-b border-line pb-5">
        <div>
          <span className="eyebrow">§ 04 · Drift</span>
          <h3 className="display-up mt-3 text-2xl text-ink">AI quality.</h3>
        </div>
        <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
          last {series.length || 30} evals · arize
        </span>
      </header>

      <div className="mt-4 flex items-baseline gap-8">
        <div>
          <p className={`display-up text-5xl tabular ${overThr ? "text-ink" : "text-ink"}`}>
            {hallPct}%
          </p>
          <p
            className={`mono mt-1 text-[0.6rem] uppercase tracking-[0.2em] ${overThr ? "text-crit" : "text-ok"}`}
          >
            hallucination {overThr ? "· over thr" : ""}
          </p>
        </div>
        <div>
          <p className="display-up text-5xl tabular text-warn">{driftPct}%</p>
          <p className="mono mt-1 text-[0.6rem] uppercase tracking-[0.2em] text-warn">
            drift
          </p>
        </div>
        <div>
          <p className="display-up text-3xl tabular text-ink-dim">{thrPct}%</p>
          <p className="mono mt-1 text-[0.6rem] uppercase tracking-[0.2em] text-ink-dim">
            threshold
          </p>
        </div>
      </div>

      <div className="mt-6 flex-1 min-h-[240px]" style={{ minWidth: 0 }}>
        <ResponsiveContainer width="100%" height={260} minWidth={0}>
          <ComposedChart
            data={series}
            margin={{ top: 8, right: 8, bottom: 8, left: -16 }}
          >
            <defs>
              <linearGradient id="g-hallu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ff5d6c" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#ff5d6c" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="g-drift" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ffb547" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#ffb547" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#232c33" strokeDasharray="2 4" />
            <XAxis
              dataKey="i"
              stroke="#6a747c"
              tickLine={false}
              axisLine={false}
              fontSize={10}
            />
            <YAxis
              stroke="#6a747c"
              tickLine={false}
              axisLine={false}
              fontSize={10}
              unit="%"
            />
            <Tooltip
              contentStyle={{
                background: "#0a0e10",
                border: "1px solid #3a444d",
                borderRadius: 12,
                fontSize: 11,
                fontFamily: "var(--font-jetbrains-mono), monospace",
                color: "#f3efe6",
              }}
              labelStyle={{
                color: "#a4adb3",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
              }}
              cursor={{ stroke: "var(--color-accent)", strokeOpacity: 0.4, strokeWidth: 1 }}
            />
            <Legend
              wrapperStyle={{
                fontFamily: "var(--font-jetbrains-mono), monospace",
                fontSize: 10,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                color: "#a4adb3",
              }}
              iconSize={8}
            />
            <Area
              type="monotone"
              dataKey="hallucination"
              stroke="#ff5d6c"
              strokeWidth={1.5}
              fill="url(#g-hallu)"
            />
            <Area
              type="monotone"
              dataKey="drift"
              stroke="#ffb547"
              strokeWidth={1.5}
              fill="url(#g-drift)"
            />
            <ReferenceLine
              y={Number(thrPct)}
              stroke="var(--color-accent)"
              strokeDasharray="4 4"
              label={{
                value: "thr",
                fill: "var(--color-accent)",
                fontSize: 10,
                fontFamily: "var(--font-jetbrains-mono), monospace",
                position: "right",
              }}
            />
            <Line
              type="monotone"
              dataKey="threshold"
              stroke="transparent"
              dot={false}
              legendType="none"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
