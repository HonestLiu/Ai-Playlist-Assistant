import { Clock, ListMusic, Pencil, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import {
  useDailyMix,
  useDeletePlaylist,
  usePlaylists,
  useRenamePlaylist,
  useSchedulerStatus,
  useTriggerDailyMix,
} from "@/hooks/useAI";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatDuration } from "@/lib/utils";

const SOURCE_LABEL: Record<string, string> = {
  daily_mix: "每日推荐",
  ai: "AI",
};

const TODAY = new Date().toISOString().slice(0, 10);

/** 把调度器的 ISO 时间渲染成「今天/明天 09:00」这类本地化文案。 */
function fmtNextRun(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  const tomorrow = new Date(now);
  tomorrow.setDate(now.getDate() + 1);
  const isTomorrow = d.toDateString() === tomorrow.toDateString();
  const hh = d.toTimeString().slice(0, 5);
  if (sameDay) return `今天 ${hh}`;
  if (isTomorrow) return `明天 ${hh}`;
  return `${d.toLocaleDateString("zh-CN")} ${hh}`;
}

export function PlaylistsPage() {
  const { data, isLoading, isError } = usePlaylists();
  const del = useDeletePlaylist();
  const rename = useRenamePlaylist();
  const dailyMix = useDailyMix();
  const scheduler = useSchedulerStatus();
  const trigger = useTriggerDailyMix();

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">加载中…</p>;
  }
  if (isError) {
    return <p className="text-sm text-destructive">加载歌单失败。</p>;
  }

  const startRename = (id: number, current: string) => {
    setEditingId(id);
    setEditName(current);
  };
  const commitRename = (id: number) => {
    const name = editName.trim();
    if (name) rename.mutate({ id, name });
    setEditingId(null);
  };

  const st = scheduler.data;
  const last = st?.last_run;

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold">
            <ListMusic className="h-5 w-5 text-primary" /> 歌单
          </h1>
          <p className="text-sm text-muted-foreground">
            AI 与每日推荐生成的歌单会同步到你的 Subsonic 服务器。
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => dailyMix.mutate({})}
          disabled={dailyMix.isPending}
        >
          <Sparkles className="mr-1.5 h-4 w-4" />
          {dailyMix.isPending ? "生成中…" : "生成今日推荐"}
        </Button>
      </div>

      {/* 自动调度状态卡片 */}
      <Card className="mb-4 bg-accent/40">
        <CardContent className="flex flex-wrap items-center gap-x-6 gap-y-2 py-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            <div className="text-sm">
              <div className="font-medium">
                每日推荐 · 自动调度
                <span
                  className={`ml-2 rounded-full px-2 py-0.5 text-[11px] ${
                    st?.enabled
                      ? "bg-primary/10 text-primary"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {st?.enabled ? "已开启" : "已关闭"}
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                下次自动生成：{fmtNextRun(st?.next_run ?? null)}（本地时间）
              </div>
            </div>
          </div>

          {last ? (
            <div className="text-xs text-muted-foreground">
              上次运行：{last.at.slice(5).replace("T", " ")}
              {last.ok ? (
                <span>
                  {" "}
                  · {last.action === "refresh" ? "已刷新" : last.action === "create" ? "已新建" : "无歌曲"}
                  {last.playlist ? `「${last.playlist}」` : ""}（{last.songs ?? 0} 首）
                </span>
              ) : (
                <span className="text-destructive"> · 失败：{last.error}</span>
              )}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">尚未自动运行过</div>
          )}

          <Button
            size="sm"
            variant="outline"
            className="ml-auto"
            disabled={trigger.isPending}
            onClick={() => trigger.mutate()}
            title="立即跑一次定时任务（与开关无关）"
          >
            <Sparkles className="mr-1.5 h-3.5 w-3.5" />
            {trigger.isPending ? "触发中…" : "立即触发调度任务"}
          </Button>
        </CardContent>
      </Card>

      {!data || data.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            还没有歌单。点右上角「生成今日推荐」，或去「AI 助手」用自然语言生成并创建一份。
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {data.map((p) => {
            const isToday =
              p.source === "daily_mix" && p.name.startsWith(`每日推荐 ${TODAY}`);
            const editing = editingId === p.id;
            const label = SOURCE_LABEL[p.source] ?? p.source;
            return (
              <Card
                key={p.id}
                className={isToday ? "border-primary/40" : undefined}
              >
                <CardContent className="flex items-center gap-3 py-4">
                  <div className="min-w-0 flex-1">
                    {editing ? (
                      <input
                        autoFocus
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") commitRename(p.id);
                          if (e.key === "Escape") setEditingId(null);
                        }}
                        className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm outline-none focus:border-primary"
                      />
                    ) : (
                      <Link
                        to={`/playlists/${p.id}`}
                        className="block truncate text-sm font-medium hover:underline"
                      >
                        {p.name}
                      </Link>
                    )}
                    <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
                      <span className="inline-flex items-center rounded-full bg-accent px-2 py-0.5 text-[11px]">
                        {label}
                      </span>
                      <span>
                        {p.song_count} 首 · {formatDuration(p.duration)}
                      </span>
                      {p.query ? <span className="truncate">· {p.query}</span> : null}
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-1">
                    {editing ? (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={rename.isPending}
                          onClick={() => commitRename(p.id)}
                        >
                          保存
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingId(null)}
                        >
                          取消
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-muted-foreground hover:text-foreground"
                          onClick={() => startRename(p.id, p.name)}
                          aria-label="重命名歌单"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-muted-foreground hover:text-destructive"
                          disabled={del.isPending}
                          onClick={() => del.mutate(p.id)}
                          aria-label="删除歌单"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
