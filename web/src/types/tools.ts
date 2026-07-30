/** 音乐库管理工具相关类型，与服务端 schemas/tools.py 一一对应。 */

export interface DuplicateSong {
  id: string;
  title: string;
  artist_name: string | null;
  album_name: string | null;
  album_id: string | null;
  duration: number | null;
  bit_rate: number | null;
  size: number | null;
  path: string | null;
  cover_art: string | null;
}

export interface DuplicateGroup {
  key: string;
  title: string;
  artist: string;
  kept: DuplicateSong;
  duplicates: DuplicateSong[];
  reason: string;
}

export interface DuplicateReport {
  total_songs: number;
  groups: DuplicateGroup[];
  removable_count: number;
  scanned_at: string;
}

export interface DeleteFailure {
  id: string;
  error: string;
}

export interface DeleteResult {
  requested: number;
  deleted: number;
  failed: DeleteFailure[];
}

export interface PlaylistDuplicateEntry {
  song_id: string;
  title: string;
  artist: string;
  occurrences: number;
}

export interface PlaylistDuplicate {
  playlist_id: string;
  subsonic_id: string;
  name: string;
  source: string;
  song_count: number;
  unique_count: number;
  duplicates: PlaylistDuplicateEntry[];
}

export interface PlaylistDuplicateReport {
  playlists: PlaylistDuplicate[];
  playlists_with_duplicates: number;
  total_removable: number;
}

export interface PlaylistCleanResult {
  playlist_id: string;
  name: string;
  removed: number;
  new_count: number;
}

export interface MetadataGap {
  category: string;
  label: string;
  count: number;
  samples: DuplicateSong[];
}

export interface MetadataGapReport {
  total_songs: number;
  gaps: MetadataGap[];
  scanned_at: string;
}
