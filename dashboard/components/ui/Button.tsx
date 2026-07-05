import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const button = cva(
  "mono inline-flex items-center justify-center gap-2 rounded-pill uppercase tracking-[0.18em] transition disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        solid: "bg-accent text-ink-dark hover:bg-accent/90",
        outline:
          "border border-line-strong text-ink-muted hover:border-accent/50 hover:text-ink",
        ghost: "text-ink-muted hover:text-ink",
      },
      size: {
        sm: "px-4 py-1.5 text-[0.65rem]",
        md: "px-6 py-3 text-[0.7rem]",
      },
    },
    defaultVariants: { variant: "solid", size: "md" },
  },
);

type ButtonProps = React.ComponentProps<"button"> & VariantProps<typeof button>;

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(button({ variant, size }), className)} {...props} />;
}

type ButtonLinkProps = React.ComponentProps<"a"> & VariantProps<typeof button>;

export function ButtonLink({ className, variant, size, ...props }: ButtonLinkProps) {
  return <a className={cn(button({ variant, size }), className)} {...props} />;
}
