import { Link } from "react-router-dom";
import { Search } from "lucide-react";

import { PlayButton } from "@/components/player/PlayButton";
import { CoverArt } from "@/components/library/CoverArt";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useBrowse } from "@/hooks/useBrowse";
import { toTrack } from "@/lib/player";
import { formatDuration } from "@/lib/utils";
import { libraryApi } from "@/services/library";

export function SongsPage() {
  const { q, setQ, items, total, hasMore, loadMore, isLoading, isFetching } = useBrowse(
    "songs",
    libraryApi.listSongs,
  );
  const tracks = items.map(toTrack);

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-medium">歌曲</h1>
          <p className="mt-1 text-sm text-muted-foreground">共 {total} 首</p>
        </div>
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜索歌曲标题"
            className="pl-8"
          />
        </div>
      </header>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">加载中…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-muted-foreground">没有匹配的歌曲</p>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted text-left text-xs text-muted-foreground">
                  <th className="w-10 px-3 py-2 text-center">#</th>
                  <th className="px-3 py-2">标题</th>
                  <th className="px-3 py-2">艺术家</th>
                  <th className="hidden px-3 py-2 sm:table-cell">专辑</th>
                  <th className="w-16 px-3 py-2 text-right">时长</th>
                </tr>
              </thead>
              <tbody>
                {items.map((s, i) => (
                  <tr key={s.id} className="border-b border-border last:border-0 hover:bg-accent">
                    <td className="px-3 py-2 text-center text-muted-foreground">
                      <PlayButton track={toTrack(s)} queue={tracks} index={i} size="icon" className="mx-auto" />
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <CoverArt
                          coverArt={s.cover_art}
                          alt={s.title}
                          className="h-8 w-8 shrink-0 rounded"
                        />
                        <span className="truncate font-medium">{s.title}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      {s.artist_id ? (
                        <Link
                          to={`/artists/${s.artist_id}`}
                          className="truncate text-muted-foreground hover:text-foreground hover:underline"
                        >
                          {s.artist_name ?? "未知艺术家"}
                        </Link>
                      ) : (
                        <span className="truncate text-muted-foreground">
                          {s.artist_name ?? "未知艺术家"}
                        </span>
                      )}
                    </td>
                    <td className="hidden px-3 py-2 sm:table-cell">
                      {s.album_id ? (
                        <Link
                          to={`/albums/${s.album_id}`}
                          className="truncate text-muted-foreground hover:text-foreground hover:underline"
                        >
                          {s.album_name ?? "未知专辑"}
                        </Link>
                      ) : (
                        <span className="truncate text-muted-foreground">
                          {s.album_name ?? "未知专辑"}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right text-muted-foreground">
                      {formatDuration(s.duration)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {hasMore ? (
            <div className="flex justify-center">
              <Button variant="outline" onClick={loadMore} disabled={isFetching}>
                {isFetching ? "加载中…" : "加载更多"}
              </Button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
