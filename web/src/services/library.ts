/** 音乐库浏览 / 同步接口调用。 */
import { request } from "@/services/http";
import type {
  AlbumDetail,
  AlbumList,
  ArtistDetail,
  ArtistList,
  ListQuery,
  Song,
  SongList,
  SyncState,
} from "@/types/library";

function buildQuery(params: ListQuery): string {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  if (params.artist_id) sp.set("artist_id", params.artist_id);
  if (params.album_id) sp.set("album_id", params.album_id);
  if (params.limit != null) sp.set("limit", String(params.limit));
  if (params.offset != null) sp.set("offset", String(params.offset));
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const libraryApi = {
  sync: () => request<SyncState>("/library/sync", { method: "POST" }),
  syncStatus: () =>
    request<SyncState | { status: "never" }>("/library/sync/status"),
  listArtists: (params: ListQuery = {}) =>
    request<ArtistList>(`/artists${buildQuery(params)}`),
  getArtist: (id: string) => request<ArtistDetail>(`/artists/${id}`),
  listAlbums: (params: ListQuery = {}) =>
    request<AlbumList>(`/albums${buildQuery(params)}`),
  getAlbum: (id: string) => request<AlbumDetail>(`/albums/${id}`),
  listSongs: (params: ListQuery = {}) =>
    request<SongList>(`/songs${buildQuery(params)}`),
  getSong: (id: string) => request<Song>(`/songs/${id}`),
};

export const libraryKeys = {
  syncStatus: ["library", "sync", "status"] as const,
  artists: (params: ListQuery) => ["artists", params] as const,
  artist: (id: string) => ["artists", "detail", id] as const,
  albums: (params: ListQuery) => ["albums", params] as const,
  album: (id: string) => ["albums", "detail", id] as const,
  songs: (params: ListQuery) => ["songs", params] as const,
  song: (id: string) => ["songs", "detail", id] as const,
};
