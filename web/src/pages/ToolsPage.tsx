import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Lock, Trash2, Wrench } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn, formatDuration, formatSize } from "@/lib/utils";
import {
  useCleanPlaylist,
  useDeleteDuplicates,
  useDuplicates,
  useMetadataGaps,
  usePlaylistDuplicates,
} from "@/hooks/useTools";
import type {
  DeleteResult,
  DuplicateGroup,
  DuplicateSong,
  MetadataGap,
  PlaylistDuplicate,
} from "@/types/tools";

/* ====================================================================== */
/* 通用小组件                                                              */
/* ====================================================================== */

function ConfirmDialog({
  open,
  title,
  description,
  confirmText,
  onConfirm,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  description?: string;
  confirmText: string;
  onConfirm: () => void;
  onClose: () => void;
  children: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-lg border border-border bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-border p-5">
          <h3 className="text-base font-medium">{title}</h3>
          {description ? (
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          ) : null}
        </div>
        <div className="max-h-[50vh] overflow-y-auto p-5">{children}</div>
        <div className="flex justify-end gap-2 border-t border-border p-4">
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}

/** 一首可勾选的「待清理」副本行。 */
function DupRow({
  song,
  checked,
  onToggle,
}: {
  song: DuplicateSong;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 hover:bg-accent">
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggle}
        className="h-4 w-4 shrink-0"
        style={{ accentColor: "var(--primary)" }}
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm">{song.title}</p>
        <p className="truncate text-xs text-muted-foreground">
          {[song.album_name, song.artist_name].filter(Boolean).join(" · ") || "—"}
        </p>
      </div>
      <div className="shrink-0 text-right text-xs text-muted-foreground">
        <p>{formatDuration(song.duration)}</p>
        <p>
          {[
            song.bit_rate ? `${song.bit_rate}kbps` : "",
            formatSize(song.size),
          ]
            .filter(Boolean)
            .join(" · ") || "—"}
        </p>
      </div>
    </label>
  );
}

/** 一首被标记为「保留」的歌曲行。 */
function KeepRow({ song }: { song: DuplicateSong }) {
  return (
    <div className="flex items-center gap-3 rounded-md bg-accent/40 px-2 py-2">
      <Lock className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{song.title}</p>
        <p className="truncate text-xs text-muted-foreground">
          {[song.album_name, song.artist_name].filter(Boolean).join(" · ") || "—"}
        </p>
      </div>
      <StatusBadge tone="success">保留</StatusBadge>
    </div>
  );
}

/* ====================================================================== */
/* 卡片一：重复歌曲检测                                                     */
/* ====================================================================== */

function DuplicatesCard() {
  const { data, isLoading, isError, refetch } = useDuplicates();
  const del = useDeleteDuplicates();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [result, setResult] = useState<DeleteResult | null>(null);

  const allDupIds = useMemo(
    () => (data ? data.groups.flatMap((g) => g.duplicates.map((s) => s.id)) : []),
    [data],
  );

  // 数据加载/变化时，默认勾选全部可清理副本
  useEffect(() => {
    setSelected(new Set(allDupIds));
    setResult(null);
  }, [allDupIds]);

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  const selectAll = () => setSelected(new Set(allDupIds));
  const clearAll = () => setSelected(new Set());

  const selectedCount = selected.size;
  const selectedSongs = useMemo(() => {
    if (!data) return [];
    const map = new Map<string, DuplicateSong>();
    for (const g of data.groups) {
      map.set(g.kept.id, g.kept);
      for (const s of g.duplicates) map.set(s.id, s);
    }
    return allDupIds.filter((id) => selected.has(id)).map((id) => map.get(id)!);
  }, [data, allDupIds, selected]);

  const confirmDelete = () => {
    const ids = selectedSongs.map((s) => s.id);
    del.mutate(ids, {
      onSuccess: (res) => {
        setResult(res);
        setConfirmOpen(false);
      },
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>重复歌曲检测</CardTitle>
            <CardDescription>
              基于本地曲库分析「同一音轨多次出现」的疑似重复，可勾选后一键清理
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => void refetch()}>
            重新扫描
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">正在扫描曲库…</p>
        ) : isError ? (
          <p className="rounded-md border border-border bg-muted px-3 py-2 text-sm text-muted-foreground">
            扫描失败，请确认曲库已同步
          </p>
        ) : data && data.groups.length === 0 ? (
          <p className="rounded-md border border-border bg-muted px-3 py-2 text-sm text-muted-foreground">
            未检测到重复歌曲 🎉
          </p>
        ) : data ? (
          <>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
              <span>
                曲库共 <strong>{data.total_songs}</strong> 首
              </span>
              <span>
                重复组 <strong>{data.groups.length}</strong> 个
              </span>
              <span>
                可清理副本 <strong>{data.removable_count}</strong> 首
              </span>
            </div>

            {result ? (
              <p
                className={cn(
                  "rounded-md border px-3 py-2 text-sm",
                  result.failed.length === 0
                    ? "border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400"
                    : "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400",
                )}
              >
                删除完成：成功 {result.deleted} 首
                {result.failed.length > 0 ? `，失败 ${result.failed.length} 首` : ""}
                {result.failed.length > 0
                  ? `（失败多为权限不足或非管理员账号，可在 Subsonic 客户端手动处理）`
                  : ""}
              </p>
            ) : null}

            <div className="max-h-[55vh] space-y-3 overflow-y-auto pr-1">
              {data.groups.map((g) => (
                <GroupBlock
                  key={g.key}
                  group={g}
                  selected={selected}
                  onToggle={toggle}
                />
              ))}
            </div>

            <div className="sticky bottom-0 flex items-center justify-between gap-3 border-t border-border bg-card pt-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>已选 {selectedCount} 首</span>
                <button
                  type="button"
                  className="text-xs text-primary hover:underline"
                  onClick={selectAll}
                >
                  全选
                </button>
                <button
                  type="button"
                  className="text-xs text-muted-foreground hover:underline"
                  onClick={clearAll}
                >
                  清空
                </button>
              </div>
              <Button
                variant="destructive"
                size="sm"
                disabled={selectedCount === 0 || del.isPending}
                onClick={() => setConfirmOpen(true)}
              >
                <Trash2 className="h-4 w-4" />
                {del.isPending ? "删除中…" : `一键删除（${selectedCount}）`}
              </Button>
            </div>
          </>
        ) : null}
      </CardContent>

      <ConfirmDialog
        open={confirmOpen}
        title="确认删除重复歌曲？"
        description={`即将从 Subsonic 服务器删除 ${selectedSongs.length} 首歌曲文件，此操作不可逆。`}
        confirmText={`删除 ${selectedSongs.length} 首`}
        onConfirm={confirmDelete}
        onClose={() => setConfirmOpen(false)}
      >
        <p className="mb-3 text-sm text-muted-foreground">
          以下歌曲将被永久删除（保留歌曲不会列出）：
        </p>
        <div className="space-y-1">
          {selectedSongs.map((s) => (
            <div key={s.id} className="flex items-center justify-between gap-2 text-sm">
              <span className="truncate">
                {s.title}
                <span className="ml-2 text-xs text-muted-foreground">
                  {[s.artist_name, s.album_name].filter(Boolean).join(" · ")}
                </span>
              </span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {formatDuration(s.duration)}
              </span>
            </div>
          ))}
        </div>
      </ConfirmDialog>
    </Card>
  );
}

function GroupBlock({
  group,
  selected,
  onToggle,
}: {
  group: DuplicateGroup;
  selected: Set<string>;
  onToggle: (id: string) => void;
}) {
  return (
    <div className="rounded-md border border-border">
      <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">
            {group.title} — {group.artist}
          </p>
          <p className="truncate text-xs text-muted-foreground">{group.reason}</p>
        </div>
        <StatusBadge tone="warning">{group.duplicates.length + 1} 首</StatusBadge>
      </div>
      <div className="space-y-1 p-2">
        <KeepRow song={group.kept} />
        {group.duplicates.map((s) => (
          <DupRow
            key={s.id}
            song={s}
            checked={selected.has(s.id)}
            onToggle={() => onToggle(s.id)}
          />
        ))}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* 卡片二：歌单去重                                                         */
/* ====================================================================== */

function PlaylistDupCard() {
  const { data, isLoading, isError } = usePlaylistDuplicates();
  const clean = useCleanPlaylist();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [done, setDone] = useState<Record<string, number>>({});

  const toggleExpand = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  if (isLoading) return <Card><CardContent><p className="text-sm text-muted-foreground">正在扫描歌单…</p></CardContent></Card>;
  if (isError) return <Card><CardContent><p className="text-sm text-muted-foreground">扫描失败</p></CardContent></Card>;
  if (!data) return null;

  const dirty = data.playlists.filter((p) => p.duplicates.length > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>歌单去重</CardTitle>
        <CardDescription>
          找出歌单内重复出现的歌曲（同 ID 或同 标题+艺术家），一键保留首次出现
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          <span>
            含重复的歌单 <strong>{data.playlists_with_duplicates}</strong> 个
          </span>
          <span>
            可移除重复 <strong>{data.total_removable}</strong> 条
          </span>
        </div>

        {dirty.length === 0 ? (
          <p className="rounded-md border border-border bg-muted px-3 py-2 text-sm text-muted-foreground">
            所有歌单均无重复 🎉
          </p>
        ) : (
          <div className="max-h-[55vh] space-y-2 overflow-y-auto pr-1">
            {dirty.map((p) => (
              <PlaylistDupRow
                key={p.playlist_id}
                playlist={p}
                expanded={expanded.has(p.playlist_id)}
                onToggle={() => toggleExpand(p.playlist_id)}
                onClean={() =>
                  clean.mutate(p.subsonic_id, {
                    onSuccess: (res) => setDone((d) => ({ ...d, [p.playlist_id]: res.removed })),
                  })
                }
                cleaning={clean.isPending && clean.variables === p.subsonic_id}
                removed={done[p.playlist_id]}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PlaylistDupRow({
  playlist,
  expanded,
  onToggle,
  onClean,
  cleaning,
  removed,
}: {
  playlist: PlaylistDuplicate;
  expanded: boolean;
  onToggle: () => void;
  onClean: () => void;
  cleaning: boolean;
  removed?: number;
}) {
  return (
    <div className="rounded-md border border-border">
      <div className="flex items-center justify-between gap-2 px-3 py-2">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-2 text-left"
          onClick={onToggle}
        >
          <ChevronDown
            className={cn("h-4 w-4 shrink-0 text-muted-foreground transition-transform", expanded && "rotate-180")}
          />
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium">{playlist.name}</span>
            <span className="block truncate text-xs text-muted-foreground">
              {playlist.song_count} 首 → 去重后 {playlist.unique_count} 首
              {removed != null ? ` · 已移除 ${removed} 条` : ""}
            </span>
          </span>
        </button>
        <Button variant="outline" size="sm" disabled={cleaning} onClick={onClean}>
          {cleaning ? "清理中…" : "清理"}
        </Button>
      </div>
      {expanded ? (
        <div className="space-y-1 border-t border-border p-2">
          {playlist.duplicates.map((d) => (
            <div key={d.song_id} className="flex items-center justify-between gap-2 px-2 text-sm">
              <span className="truncate">
                {d.title}
                <span className="ml-2 text-xs text-muted-foreground">{d.artist}</span>
              </span>
              <StatusBadge tone="warning">×{d.occurrences}</StatusBadge>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/* ====================================================================== */
/* 卡片三：信息缺失扫描                                                     */
/* ====================================================================== */

function MetadataGapsCard() {
  const { data, isLoading, isError } = useMetadataGaps();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  if (isLoading) return <Card><CardContent><p className="text-sm text-muted-foreground">正在扫描…</p></CardContent></Card>;
  if (isError) return <Card><CardContent><p className="text-sm text-muted-foreground">扫描失败</p></CardContent></Card>;
  if (!data) return null;

  const toggle = (cat: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });

  return (
    <Card>
      <CardHeader>
        <CardTitle>信息缺失扫描</CardTitle>
        <CardDescription>统计缺少封面 / 年份 / 流派 / 专辑归属的歌曲</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm">
          曲库共 <strong>{data.total_songs}</strong> 首
        </p>
        <div className="space-y-2">
          {data.gaps.map((gap) => (
            <GapRow
              key={gap.category}
              gap={gap}
              expanded={expanded.has(gap.category)}
              onToggle={() => toggle(gap.category)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function GapRow({
  gap,
  expanded,
  onToggle,
}: {
  gap: MetadataGap;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="rounded-md border border-border">
      <div className="flex items-center justify-between gap-2 px-3 py-2">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-2 text-left"
          onClick={onToggle}
        >
          <ChevronDown
            className={cn("h-4 w-4 shrink-0 text-muted-foreground transition-transform", expanded && "rotate-180")}
          />
          <span className="text-sm font-medium">{gap.label}</span>
        </button>
        <StatusBadge tone={gap.count > 0 ? "warning" : "success"}>{gap.count}</StatusBadge>
      </div>
      {expanded && gap.samples.length > 0 ? (
        <div className="max-h-48 space-y-1 overflow-y-auto border-t border-border p-2">
          {gap.samples.map((s) => (
            <div key={s.id} className="flex items-center justify-between gap-2 px-2 text-sm">
              <span className="truncate">
                {s.title}
                <span className="ml-2 text-xs text-muted-foreground">
                  {[s.artist_name, s.album_name].filter(Boolean).join(" · ")}
                </span>
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/* ====================================================================== */
/* 页面                                                                    */
/* ====================================================================== */

export function ToolsPage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-medium">
          <Wrench className="h-5 w-5" />
          音乐库工具箱
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          曲库整理小工具：重复歌曲清理、歌单去重、信息缺失扫描。
        </p>
      </div>

      <DuplicatesCard />
      <PlaylistDupCard />
      <MetadataGapsCard />
    </div>
  );
}
