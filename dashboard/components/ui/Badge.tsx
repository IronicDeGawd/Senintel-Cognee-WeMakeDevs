import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badge = cva(
  "mono inline-flex items-center gap-2 rounded-tag px-2 py-1 text-[0.6rem] uppercase tracking-[0.14em]",
  {
    variants: {
      variant: {
        accent: "bg-accent/15 text-accent",
        ok: "border border-ok/30 bg-ok-bg text-ok",
        warn: "border border-warn/30 bg-warn-bg text-warn",
        crit: "border border-crit/30 bg-crit-bg text-crit",
        neutral: "border border-line text-ink-dim",
      },
    },
    defaultVariants: { variant: "neutral" },
  },
);

type BadgeProps = React.ComponentProps<"span"> & VariantProps<typeof badge>;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badge({ variant }), className)} {...props} />;
}
