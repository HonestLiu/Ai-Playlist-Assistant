import { Disc3, Loader2, LogIn } from "lucide-react";
import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { useLogin, useSession } from "@/hooks/useAuth";
import { HttpError } from "@/services/http";

export function LoginPage() {
  const session = useSession();
  const login = useLogin();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 一个账号都没有 → 该走启动引导而不是登录
  if (session.data?.needs_bootstrap) return <Navigate to="/setup" replace />;
  if (session.data?.authenticated) {
    return <Navigate to={location.state?.from ?? "/"} replace />;
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await login.mutateAsync({ username, password, remember });
      navigate(location.state?.from ?? "/", { replace: true });
    } catch (err) {
      setError(err instanceof HttpError ? err.message : "登录失败，请重试");
    }
  };

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Disc3 className="h-6 w-6" />
          </span>
          <h1 className="text-lg font-medium">歌单助手</h1>
          <p className="text-sm text-muted-foreground">登录后继续使用</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>登录</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-4" onSubmit={submit}>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="login-username">用户名</Label>
                <Input
                  id="login-username"
                  autoComplete="username"
                  autoFocus
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="login-password">密码</Label>
                <Input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              <label className="flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  className="h-3.5 w-3.5 accent-[var(--primary)]"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                保持登录状态
              </label>

              {error ? <p className="text-sm text-destructive">{error}</p> : null}

              <Button
                type="submit"
                disabled={login.isPending || !username || !password}
                className="w-full"
              >
                {login.isPending ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <LogIn className="mr-1.5 h-4 w-4" />
                )}
                登录
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
