import { Badge } from "@/components/ui/Badge";
import { SectionHeader } from "@/components/ui/SectionHeader";

const stack = [
  "Gemini 2.5 Flash · Vertex AI",
  "Google ADK 2.x",
  "Dynatrace MCP v1.8.7",
  "GitLab Duo MCP",
  "Cloud Run",
  "Firestore",
  "Next.js 16",
  "SWR · 5s poll",
];

export function TechEcosystem() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1440px] px-6 py-24 lg:px-10 lg:py-32">
        <SectionHeader
          eyebrow="§ 03 · Technology"
          title={
            <>
              <span className="display">One agent runtime,</span> everything
              connected.
            </>
          }
        />
        <p className="mt-6 max-w-2xl text-base leading-relaxed text-ink-muted">
          Real partner MCP servers — not wrappers. Each pillar speaks to its
          tool over its native protocol, every reasoning step runs on Gemini,
          and every finding lands as the same <code>Signal</code> envelope.
        </p>

        <div className="mt-16 overflow-hidden rounded-card-lg border border-line card-depth">
          <div className="border-b border-line p-6 lg:p-8">
            <div className="mono flex items-center justify-between text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
              <span>infra/architecture.svg</span>
              <span className="text-accent">live · 6 services on cloud run</span>
            </div>
          </div>

          <div className="p-6 lg:p-12">
            <svg
              viewBox="0 0 1200 600"
              className="h-auto w-full"
              role="img"
              aria-label="SentinelAI topology — three pillar agents on Cloud Run talk to Dynatrace, GitLab and Arize over MCP, reason with Gemini, and emit Signal envelopes into Firestore, polled live by the dashboard"
            >
              <defs>
                <pattern
                  id="dotgrid"
                  width="24"
                  height="24"
                  patternUnits="userSpaceOnUse"
                >
                  <circle cx="1" cy="1" r="1" fill="#232c33" />
                </pattern>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--color-accent)" />
                </marker>
              </defs>

              <rect width="1200" height="600" fill="url(#dotgrid)" />

              {/* Cloud Run boundary around the pillar services */}
              <rect
                x={44}
                y={52}
                width={292}
                height={500}
                rx={28}
                fill="transparent"
                stroke="#3a444d"
                strokeWidth="1"
                strokeDasharray="6 6"
              />
              <text
                x={60}
                y={542}
                className="mono"
                fill="#6a747c"
                fontSize="9"
                letterSpacing="2"
              >
                CLOUD RUN · GATEWAY / POLLER / EVAL-RUNNER
              </text>

              {/* Pillars — Dynatrace first */}
              <Node x={60} y={80} w={260} h={120} title="Production Sentinel" sub="Dynatrace MCP · stdio" lead />
              <Node x={60} y={240} w={260} h={120} title="Code Guardian" sub="GitLab Duo MCP + REST" />
              <Node x={60} y={400} w={260} h={120} title="AI Quality Gate" sub="Arize-shaped evals" />

              {/* Signal envelope */}
              <g>
                <rect
                  x={460}
                  y={210}
                  width={260}
                  height={180}
                  rx={24}
                  fill="#0a0e10"
                  stroke="var(--color-accent)"
                  strokeWidth="1.5"
                />
                <text
                  x={590}
                  y={250}
                  textAnchor="middle"
                  className="mono"
                  fill="var(--color-accent)"
                  fontSize="11"
                  letterSpacing="3"
                >
                  SIGNAL ENVELOPE
                </text>
                <text
                  x={590}
                  y={290}
                  textAnchor="middle"
                  fill="#f3efe6"
                  fontSize="22"
                  fontFamily="ui-serif, Georgia, serif"
                  fontStyle="italic"
                >
                  pillar · status
                </text>
                <text
                  x={590}
                  y={320}
                  textAnchor="middle"
                  fill="#f3efe6"
                  fontSize="22"
                  fontFamily="ui-serif, Georgia, serif"
                  fontStyle="italic"
                >
                  headline · detail
                </text>
                <text
                  x={590}
                  y={355}
                  textAnchor="middle"
                  className="mono"
                  fill="#6a747c"
                  fontSize="10"
                  letterSpacing="2"
                >
                  /shared/models.py
                </text>
              </g>

              {/* Firestore */}
              <Node x={860} y={160} w={260} h={120} title="Firestore" sub="signals collection" />

              {/* Dashboard */}
              <Node x={860} y={320} w={260} h={120} title="Dashboard" sub="Next.js · Cloud Run" />

              {/* Pillar → Signal arrows, with protocol labels */}
              <Arrow x1={320} y1={140} x2={460} y2={260} />
              <EdgeLabel x={390} y={185} text="DAVIS PROBLEMS" />
              <Arrow x1={320} y1={300} x2={460} y2={300} />
              <EdgeLabel x={390} y={290} text="MR WEBHOOKS" />
              <Arrow x1={320} y1={460} x2={460} y2={340} />
              <EdgeLabel x={390} y={420} text="EVAL RUNS" />

              {/* Signal → storage → UI */}
              <Arrow x1={720} y1={260} x2={860} y2={210} />
              <Arrow x1={720} y1={340} x2={860} y2={380} />
              <Arrow x1={860} y1={250} x2={860} y2={320} dash />
              <EdgeLabel x={838} y={290} text="SWR · 5S POLL" anchor="end" />

              {/* Gemini lane — reasoning feeds every pillar */}
              <g opacity="0.7">
                <rect
                  x={460}
                  y={60}
                  width={260}
                  height={56}
                  rx={28}
                  fill="transparent"
                  stroke="#3a444d"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={590}
                  y={94}
                  textAnchor="middle"
                  className="mono"
                  fill="#a4adb3"
                  fontSize="11"
                  letterSpacing="3"
                >
                  GEMINI · VERTEX AI · ADC
                </text>
              </g>
              <line
                x1={590}
                y1={116}
                x2={590}
                y2={210}
                stroke="#3a444d"
                strokeWidth="1"
                strokeDasharray="3 4"
              />
              <g opacity="0.45">
                <line x1={460} y1={88} x2={324} y2={110} stroke="#3a444d" strokeWidth="1" strokeDasharray="3 4" />
                <line x1={460} y1={94} x2={324} y2={262} stroke="#3a444d" strokeWidth="1" strokeDasharray="3 4" />
                <line x1={460} y1={100} x2={324} y2={420} stroke="#3a444d" strokeWidth="1" strokeDasharray="3 4" />
              </g>
            </svg>
          </div>
        </div>

        {/* Stack — partner names as text, never logos */}
        <div className="mt-8 flex flex-wrap gap-2.5">
          {stack.map((s) => (
            <Badge key={s} variant="neutral">
              {s}
            </Badge>
          ))}
        </div>
      </div>
    </section>
  );
}

function EdgeLabel({
  x,
  y,
  text,
  anchor = "middle",
}: {
  x: number;
  y: number;
  text: string;
  anchor?: "middle" | "end";
}) {
  return (
    <text
      x={x}
      y={y}
      textAnchor={anchor}
      className="mono"
      fill="#6a747c"
      fontSize="9"
      letterSpacing="2"
    >
      {text}
    </text>
  );
}

function Node({
  x,
  y,
  w,
  h,
  title,
  sub,
  lead,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  title: string;
  sub: string;
  lead?: boolean;
}) {
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={20}
        fill="#161c22"
        stroke={lead ? "var(--color-accent)" : "#3a444d"}
        strokeWidth={lead ? 1.5 : 1}
      />
      {lead && (
        <rect
          x={x + 12}
          y={y + 12}
          width={4}
          height={24}
          rx={2}
          fill="var(--color-accent)"
        />
      )}
      <text
        x={x + 24}
        y={y + 48}
        fill="#f3efe6"
        fontSize="22"
        fontFamily="ui-serif, Georgia, serif"
        fontStyle="italic"
      >
        {title}
      </text>
      <text
        x={x + 24}
        y={y + h - 24}
        className="mono"
        fill="#a4adb3"
        fontSize="11"
        letterSpacing="2.5"
      >
        {sub.toUpperCase()}
      </text>
    </g>
  );
}

function Arrow({
  x1,
  y1,
  x2,
  y2,
  dash,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  dash?: boolean;
}) {
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke={dash ? "#3a444d" : "var(--color-accent)"}
      strokeWidth="1.5"
      strokeDasharray={dash ? "4 4" : undefined}
      markerEnd="url(#arrow)"
    />
  );
}
