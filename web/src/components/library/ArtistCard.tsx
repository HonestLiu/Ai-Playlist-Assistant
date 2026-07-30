import { Link } from "react-router-dom";

import type { Artist } from "@/types/library";

import { CoverArt } from "./CoverArt";

export function ArtistCard({ artist }: { artist: Artist }) {
  const name = artist.name || "未知艺术家";
  return (
    <Link
      to={`/artists/${artist.id}`}
      className="group flex flex-col gap-3 rounded-lg p-2 transition-colors hover:bg-accent"
    >
      <CoverArt
        coverArt={artist.cover_art}
        alt={name}
        className="aspect-square w-full rounded-md"
      />
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{name}</p>
        <p className="truncate text-xs text-muted-foreground">
          {artist.album_count ?? 0} 专辑 · {artist.song_count ?? 0} 歌曲
        </p>
      </div>
    </Link>
  );
}
