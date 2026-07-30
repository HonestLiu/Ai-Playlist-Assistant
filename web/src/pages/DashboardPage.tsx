import { Activity, Server, Wifi } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { useHealth, useSubsonicStatus } from "@/hooks/useSubsonic";

function Metric({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof Server;
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-5">
        <span className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-md bg-accent">
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="truncate text-sm font-medium">{value}</p>
          {hint ? <p className="mt-0.5 truncate text-xs text-muted-foreground">{hint}</p> : null}
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const health = useHealth();
  const status = useSubsonicStatus();

  const server = status.data?.server;

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div>
        <h1 className="text-xl font-medium">总览</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          确认本地服务端与 Subsonic 服务器的连接状态。
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Metric
          icon={Activity}
          label="本地服务端"
          value={health.data ? `运行中 v${health.data.version}` : health.isError ? "未启动" : "检测中"}
          hint={health.data?.app_name}
        />
        <Metric
          icon={Server}
          label="Subsonic 服务器"
          value={server?.server_type ? `${server.server_type} ${server.server_version ?? ""}` : "—"}
          hint={status.data?.url ?? "尚未配置"}
        />
        <Metric
          icon={Wifi}
          label="握手延迟"
          value={status.data?.latency_ms != null ? `${status.data.latency_ms} ms` : "—"}
          hint={status.data?.username ? `账号 ${status.data.username}` : undefined}
        />
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>连接状态</CardTitle>
              <CardDescription>
                最后检测时间{" "}
                {status.data ? new Date(status.data.checked_at).toLocaleString("zh-CN") : "—"}
              </CardDescription>
            </div>
            {status.data?.connected ? (
              <StatusBadge tone="success">正常</StatusBadge>
            ) : (
              <StatusBadge tone="danger">异常</StatusBadge>
            )}
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {status.data && !status.data.connected ? (
            <p className="rounded-md border border-border bg-muted px-3 py-2 text-sm text-muted-foreground">
              {status.data.error_message ?? "未知错误"}
              {status.data.error_code ? (
                <span className="ml-2 font-mono text-xs opacity-70">{status.data.error_code}</span>
              ) : null}
            </p>
          ) : null}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => void status.refetch()}>
              重新检测
            </Button>
            <Link to="/settings">
              <Button size="sm">去设置</Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>功能导航</CardTitle>
          <CardDescription>核心能力均已就绪，点选即可进入</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2">
            <Link
              to="/assistant"
              className="rounded-md border border-border px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted"
            >
              💬 AI 助手 · 自然语言生成歌单
            </Link>
            <Link
              to="/playlists"
              className="rounded-md border border-border px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted"
            >
              🎵 歌单 · 历史歌单与每日推荐
            </Link>
            <Link
              to="/library"
              className="rounded-md border border-border px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted"
            >
              📚 音乐库 · 同步与浏览艺术家 / 专辑 / 歌曲
            </Link>
            <Link
              to="/settings"
              className="rounded-md border border-border px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted"
            >
              ⚙️ 设置 · 服务器 / AI / 账号
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
