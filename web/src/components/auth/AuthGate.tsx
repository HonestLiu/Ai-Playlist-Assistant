import { Loader2 } from "lucide-react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useSession } from "@/hooks/useAuth";

/**
 * 路由守卫：一次 /auth/session 决定去向。
 *
 * 未初始化 → 启动引导；未登录 → 登录页；引导未完成 → 继续引导；否则放行。
 */
export function AuthGate() {
  const { data, isLoading, isError, refetch, isFetching } = useSession();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
        <p className="text-sm text-destructive">无法连接到服务端</p>
        <p className="text-sm text-muted-foreground">
          确认后端已启动（默认 http://127.0.0.1:8000）
        </p>
        <Button variant="outline" size="sm" disabled={isFetching} onClick={() => void refetch()}>
          {isFetching ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : null}
          重试
        </Button>
      </div>
    );
  }

  if (data.needs_bootstrap) return <Navigate to="/setup" replace />;

  if (!data.authenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!data.onboarding_completed) return <Navigate to="/setup" replace />;

  return <Outlet />;
}
