import { Card, CardContent } from "@/components/ui/card";

interface PlaceholderPageProps {
  title: string;
  phase: string;
  description: string;
}

/** 占位页：把后续 Phase 的信息架构先立起来，避免路由结构后期返工。 */
export function PlaceholderPage({ title, phase, description }: PlaceholderPageProps) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-medium">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      <Card>
        <CardContent className="flex flex-col items-center gap-2 py-14 text-center">
          <span className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
            {phase}
          </span>
          <p className="text-sm text-muted-foreground">该模块将在后续阶段实现</p>
        </CardContent>
      </Card>
    </div>
  );
}
