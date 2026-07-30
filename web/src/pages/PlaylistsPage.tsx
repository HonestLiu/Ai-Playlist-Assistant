import { ListMusic, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";

import { useDeletePlaylist, usePlaylists } from "@/hooks/useAI";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatDuration } from "@/lib/utils";

export function PlaylistsPage() {
  const { data, isLoading, isError } = usePlaylists();
  const del = useDeletePlaylist();

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">加载中…</p>;
  }
  if (isError) {
    return <p className="text-sm text-destructive">加载歌单失败。</p>;
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-4">
        <h1 className="flex items-center gap-2 text-xl font-semibold">
          <ListMusic className="h-5 w-5 text-primary" /> 歌单
        </h1>
        <p className="text-sm text-muted-foreground">
          AI 生成的歌单会同步到你的 Subsonic 服务器。
        </p>
      </div>

      {!data || data.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            还没有歌单。去「AI 助手」用自然语言生成并创建一份吧。
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {data.map((p) => (
            <Card key={p.id}>
              <CardContent className="flex items-center gap-4 py-4">
                <div className="min-w-0 flex-1">
                  <Link
                    to={`/playlists/${p.id}`}
                    className="block truncate text-sm font-medium hover:underline"
                  >
                    {p.name}
                  </Link>
                  <div className="mt-0.5 truncate text-xs text-muted-foreground">
                    {p.song_count} 首 · {formatDuration(p.duration)} · 来源 {p.source}
                    {p.query ? ` · ${p.query}` : ""}
                  </div>
                </div>
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
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
