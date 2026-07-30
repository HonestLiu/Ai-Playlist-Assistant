import { ArrowLeft, Play } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { PlayButton } from "@/components/player/PlayButton";
import { CoverArt } from "@/components/library/CoverArt";
import { Button } from "@/components/ui/button";
import { useAlbum } from "@/hooks/useLibrary";
import { toTrack } from "@/lib/player";
import { formatDuration } from "@/lib/utils";
import { usePlayerStore } from "@/stores/player";

export function AlbumDetailPage() {
  const { id = "" } = useParams();
  const { data, isLoading } = useAlbum(id);

  if (isLoading) return <p className="text-sm text-muted-foreground">加载中…</p>;
  if (!data) return <p className="text-sm text-muted-foreground">未找到该专辑</p>;

  const name = data.name || "未知专辑";
  const tracks = data.songs.map(toTrack);

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <Link
        to="/albums"
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        返回专辑
      </Link>

      <div className="flex items-center gap-4">
        <CoverArt coverArt={data.cover_art} alt={name} className="h-28 w-28 rounded-md" />
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-medium">{name}</h1>
          {data.artist_id ? (
            <Link
              to={`/artists/${data.artist_id}`}
              className="mt-1 block truncate text-sm text-muted-foreground hover:text-foreground hover:underline"
            >
              {data.artist_name ?? "未知艺术家"}
            </Link>
          ) : (
            <p className="mt-1 truncate text-sm text-muted-foreground">
              {data.artist_name ?? "未知艺术家"}
            </p>
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            {data.song_count ?? 0} 首 · {formatDuration(data.duration)}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="shrink-0"
          onClick={() => usePlayerStore.getState().setQueue(tracks, 0)}
        >
          <Play className="mr-1.5 h-4 w-4" /> 播放全部
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted text-left text-xs text-muted-foreground">
              <th className="w-10 px-3 py-2 text-center">#</th>
              <th className="px-3 py-2">标题</th>
              <th className="w-20 px-3 py-2 text-right">时长</th>
            </tr>
          </thead>
          <tbody>
            {data.songs.map((s, i) => (
              <tr key={s.id} className="border-b border-border last:border-0 hover:bg-accent">
                <td className="px-3 py-2 text-center text-muted-foreground">
                  <PlayButton track={toTrack(s)} queue={tracks} index={i} size="icon" className="mx-auto" />
                </td>
                <td className="px-3 py-2 font-medium">{s.title}</td>
                <td className="px-3 py-2 text-right text-muted-foreground">
                  {formatDuration(s.duration)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
