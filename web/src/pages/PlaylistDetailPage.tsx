import { ArrowLeft, Play, Trash2 } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { PlayButton } from "@/components/player/PlayButton";
import { useDeletePlaylist, usePlaylist } from "@/hooks/useAI";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toTrack } from "@/lib/player";
import { formatDuration } from "@/lib/utils";
import { usePlayerStore } from "@/stores/player";

export function PlaylistDetailPage() {
  const { id } = useParams();
  const playlistId = Number(id);
  const { data, isLoading, isError } = usePlaylist(playlistId);
  const del = useDeletePlaylist();
  const navigate = useNavigate();

  if (isLoading) return <p className="text-sm text-muted-foreground">加载中…</p>;
  if (isError || !data)
    return <p className="text-sm text-destructive">歌单不存在或加载失败。</p>;

  const tracks = data.songs.map(toTrack);

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        to="/playlists"
        className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> 返回歌单列表
      </Link>

      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold">{data.name}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data.song_count} 首 · {formatDuration(data.duration)} · 来源 {data.source}
          </p>
          {data.query && (
            <p className="mt-1 text-xs text-muted-foreground">需求：{data.query}</p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          className="shrink-0"
          onClick={() => usePlayerStore.getState().setQueue(tracks, 0)}
        >
          <Play className="mr-1.5 h-4 w-4" /> 播放全部
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="shrink-0 text-destructive hover:bg-destructive/10"
          disabled={del.isPending}
          onClick={async () => {
            await del.mutateAsync(data.id);
            navigate("/playlists");
          }}
        >
          <Trash2 className="mr-1.5 h-4 w-4" /> 删除
        </Button>
      </div>

      {data.songs.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            该歌单在本地没有歌曲明细（可能由外部客户端创建）。
          </CardContent>
        </Card>
      ) : (
        <ol className="divide-y divide-border rounded-xl border border-border bg-card">
          {data.songs.map((song, i) => (
            <li key={song.id} className="flex items-start gap-3 px-4 py-2.5">
              <span className="mt-0.5 flex w-8 shrink-0 items-center justify-end gap-1 text-xs text-muted-foreground">
                <PlayButton track={tracks[i]} queue={tracks} index={i} size="icon" className="-mr-1" />
                <span>{i + 1}</span>
              </span>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{song.title}</div>
                <div className="truncate text-xs text-muted-foreground">
                  {song.artist_name ?? "未知艺术家"}
                  {song.album_name ? ` · ${song.album_name}` : ""}
                  {song.year ? ` · ${song.year}` : ""}
                  {song.duration ? ` · ${formatDuration(song.duration)}` : ""}
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
