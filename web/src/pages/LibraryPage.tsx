import { AlertCircle, Disc3, ListMusic, Music2, RefreshCw } from "lucide-react";
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
import { useSubsonicStatus } from "@/hooks/useSubsonic";
import { useSyncStatus, useTriggerSync } from "@/hooks/useLibrary";
import type { SyncState } from "@/types/library";

function StatLink({
  to,
  icon: Icon,
  label,
  value,
}: {
  to: string;
  icon: typeof Disc3;
  label: string;
  value: number | string;
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 rounded-lg border border-border p-4 transition-colors hover:bg-accent"
    >
      <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accent">
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <p className="text-lg font-medium">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </Link>
  );
}

function statusTone(status: string): "success" | "danger" | "muted" | "warning" {
  if (status === "success") return "success";
  if (status === "failed") return "danger";
  if (status === "running" || status === "queued") return "warning";
  return "muted";
}

function SyncBody({ data }: { data: SyncState | { status: "never" } | undefined }) {
  const trigger = useTriggerSync();

  if (!data) return null;

  if ("status" in data && data.status === "never") {
    return (
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">还没有同步过音乐库，点下面的按钮开始。</p>
        <div>
          <Button onClick={() => trigger.mutate()} disabled={trigger.isPending}>
            <RefreshCw className={trigger.isPending ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
            {trigger.isPending ? "同步中…" : "同步音乐库"}
          </Button>
        </div>
      </CardContent>
    );
  }

  const state = data as SyncState;
  const syncing = state.status === "running" || state.status === "queued";
  return (
    <CardContent className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge tone={statusTone(state.status)}>
          {state.status === "running"
            ? "同步中"
            : state.status === "queued"
              ? "排队中"
              : state.status === "success"
                ? "完成"
                : state.status === "failed"
                  ? "失败"
                  : state.status}
        </StatusBadge>
        <span className="text-sm text-muted-foreground">
          {state.artists_synced} 艺术家 · {state.albums_synced} 专辑 · {state.songs_synced} 歌曲
        </span>
        {state.finished_at ? (
          <span className="text-xs text-muted-foreground">
            {new Date(state.finished_at).toLocaleString("zh-CN")}
          </span>
        ) : null}
      </div>

      {state.error ? (
        <p className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          {state.error}
        </p>
      ) : null}

      <div>
        <Button onClick={() => trigger.mutate()} disabled={trigger.isPending || syncing}>
          <RefreshCw className={(trigger.isPending || syncing) ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
          {syncing ? "同步进行中…" : trigger.isPending ? "提交中…" : "重新同步"}
        </Button>
      </div>
    </CardContent>
  );
}

export function LibraryPage() {
  const status = useSubsonicStatus();
  const sync = useSyncStatus();

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div>
        <h1 className="text-xl font-medium">音乐库</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          把 Subsonic 服务器上的音乐库同步到本地，供 AI 选歌与浏览。
        </p>
      </div>

      {!status.data?.connected ? (
        <Card>
          <CardContent className="py-6 text-sm text-muted-foreground">
            尚未连接到 Subsonic 服务器，请先在
            <Link to="/settings" className="mx-1 text-primary underline">
              设置
            </Link>
            页配置。
          </CardContent>
        </Card>
      ) : (
        (() => {
          const sc =
            sync.data && "artists_synced" in sync.data && (sync.data as SyncState).status === "success"
              ? (sync.data as SyncState)
              : null;
          return (
            <div className="grid gap-4 sm:grid-cols-3">
              <StatLink to="/artists" icon={Music2} label="艺术家" value={sc ? sc.artists_synced : "—"} />
              <StatLink to="/albums" icon={Disc3} label="专辑" value={sc ? sc.albums_synced : "—"} />
              <StatLink to="/songs" icon={ListMusic} label="歌曲" value={sc ? sc.songs_synced : "—"} />
            </div>
          );
        })()
      )}

      <Card>
        <CardHeader>
          <CardTitle>同步状态</CardTitle>
          <CardDescription>全量同步会清空并重新拉取整个音乐库</CardDescription>
        </CardHeader>
        <SyncBody data={sync.data} />
      </Card>
    </div>
  );
}
