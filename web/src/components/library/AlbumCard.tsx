import { Link } from "react-router-dom";

import type { Album } from "@/types/library";

import { CoverArt } from "./CoverArt";

export function AlbumCard({ album }: { album: Album }) {
  const name = album.name || "未知专辑";
  return (
    <Link
      to={`/albums/${album.id}`}
      className="group flex flex-col gap-3 rounded-lg p-2 transition-colors hover:bg-accent"
    >
      <CoverArt
        coverArt={album.cover_art}
        alt={name}
        className="aspect-square w-full rounded-md"
      />
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{name}</p>
        <p className="truncate text-xs text-muted-foreground">
          {album.artist_name ?? "未知艺术家"}
        </p>
      </div>
    </Link>
  );
}
