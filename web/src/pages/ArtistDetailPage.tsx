import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { AlbumCard } from "@/components/library/AlbumCard";
import { CoverArt } from "@/components/library/CoverArt";
import { useArtist } from "@/hooks/useLibrary";

export function ArtistDetailPage() {
  const { id = "" } = useParams();
  const { data, isLoading } = useArtist(id);

  if (isLoading) return <p className="text-sm text-muted-foreground">加载中…</p>;
  if (!data) return <p className="text-sm text-muted-foreground">未找到该艺术家</p>;

  const name = data.name || "未知艺术家";

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <Link
        to="/artists"
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        返回艺术家
      </Link>

      <div className="flex items-center gap-4">
        <CoverArt coverArt={data.cover_art} alt={name} className="h-28 w-28 rounded-md" />
        <div>
          <h1 className="text-2xl font-medium">{name}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data.album_count ?? 0} 专辑 · {data.song_count ?? 0} 歌曲
          </p>
        </div>
      </div>

      <h2 className="text-lg font-medium">专辑</h2>
      {data.albums.length === 0 ? (
        <p className="text-sm text-muted-foreground">暂无专辑</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {data.albums.map((a) => (
            <AlbumCard key={a.id} album={a} />
          ))}
        </div>
      )}
    </div>
  );
}
