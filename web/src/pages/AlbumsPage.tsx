import { Search } from "lucide-react";

import { AlbumCard } from "@/components/library/AlbumCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useBrowse } from "@/hooks/useBrowse";
import { libraryApi } from "@/services/library";

export function AlbumsPage() {
  const { q, setQ, items, total, hasMore, loadMore, isLoading, isFetching } = useBrowse(
    "albums",
    libraryApi.listAlbums,
  );

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-medium">专辑</h1>
          <p className="mt-1 text-sm text-muted-foreground">共 {total} 张 · 点击查看歌曲</p>
        </div>
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜索专辑"
            className="pl-8"
          />
        </div>
      </header>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">加载中…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-muted-foreground">没有匹配的专辑</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {items.map((a) => (
              <AlbumCard key={a.id} album={a} />
            ))}
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
