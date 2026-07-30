/** 音乐库相关类型，与服务端 schemas 一一对应。 */

export interface Artist {
  id: string;
  name: string;
  album_count: number | null;
  song_count: number | null;
  cover_art: string | null;
}

export interface Album {
  id: string;
  name: string;
  artist_id: string | null;
  artist_name: string | null;
  cover_art: string | null;
  song_count: number | null;
  duration: number | null;
  year: number | null;
  genre: string | null;
}

export interface Song {
  id: string;
  title: string;
  album_id: string | null;
  album_name: string | null;
  artist_id: string | null;
  artist_name: string | null;
  track: number | null;
  year: number | null;
  genre: string | null;
  duration: number | null;
  bit_rate: number | null;
  size: number | null;
  content_type: string | null;
  suffix: string | null;
  path: string | null;
  cover_art: string | null;
}

export interface ArtistDetail extends Artist {
  albums: Album[];
}

export interface AlbumDetail extends Album {
  songs: Song[];
}

export interface SyncState {
  id: number | null;
  scope: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  artists_synced: number;
  albums_synced: number;
  songs_synced: number;
  error: string | null;
}

export interface ArtistList {
  items: Artist[];
  total: number;
  limit: number;
  offset: number;
}

export interface AlbumList {
  items: Album[];
  total: number;
  limit: number;
  offset: number;
}

export interface SongList {
  items: Song[];
  total: number;
  limit: number;
  offset: number;
}

export interface ListQuery {
  q?: string;
  artist_id?: string;
  album_id?: string;
  limit?: number;
  offset?: number;
}
