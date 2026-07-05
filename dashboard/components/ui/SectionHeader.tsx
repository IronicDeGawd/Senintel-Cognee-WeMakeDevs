import { cn } from "@/lib/utils";

/** Eyebrow + display heading + optional right-aligned meta slot.
 * The repeating section-header pattern across landing and dashboard. */
export function SectionHeader({
  eyebrow,
  title,
  meta,
  className,
}: {
  eyebrow: string;
  title: React.ReactNode;
  meta?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between",
        className,
      )}
    >
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="display-up mt-3 text-3xl text-ink sm:text-4xl">{title}</h2>
      </div>
      {meta && <div className="shrink-0">{meta}</div>}
    </div>
  );
}
