import { cn } from "@/lib/utils";

export type StatusTone = "success" | "danger" | "warning" | "muted";

const toneStyles: Record<StatusTone, string> = {
  success: "border-[color-mix(in_oklab,var(--success)_40%,transparent)] text-[var(--success)]",
  danger:
    "border-[color-mix(in_oklab,var(--destructive)_40%,transparent)] text-[var(--destructive)]",
  warning: "border-[color-mix(in_oklab,var(--warning)_40%,transparent)] text-[var(--warning)]",
  muted: "border-border text-muted-foreground",
};

interface StatusBadgeProps {
  tone: StatusTone;
  children: React.ReactNode;
  className?: string;
}

export function StatusBadge({ tone, children, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        toneStyles[tone],
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children}
    </span>
  );
}
