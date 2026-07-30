/** AI 推荐与歌单相关类型，对应服务端 schemas。 */

export interface PlaylistIntent {
  summary: string;
  mood: string[] | null;
  language: string[] | null;
  genres: string[] | null;
  decade: number | null;
  min_year: number | null;
  max_year: number | null;
  activities: string[] | null;
  energy: string | null;
  keywords: string[] | null;
  exclude_keywords: string[] | null;
  target_size: number;
}

export interface RecommendedSong {
  id: string;
  title: string;
  artist_name: string | null;
  album_name: string | null;
  year: number | null;
  duration: number | null;
  reason: string | null;
}

export interface PlaylistRef {
  id: string;
  subsonic_id: string;
  name: string;
}

export interface RecommendationResult {
  query: string;
  intent: PlaylistIntent;
  provider: string;
  total_candidates: number;
  songs: RecommendedSong[];
  total_duration: number;
  playlist: PlaylistRef | null;
}

export interface Playlist {
  id: number;
  subsonic_id: string;
  name: string;
  description: string | null;
  source: string;
  query: string | null;
  song_count: number;
  duration: number;
  created_at: string;
}

export interface PlaylistDetail extends Playlist {
  songs: import("./library").Song[];
}

export interface LLMConfigOut {
  provider: string;
  base_url: string;
  has_api_key: boolean;
  model: string;
  temperature: number | null;
  source: string;
}

export interface LLMConfigIn {
  provider: string;
  base_url?: string;
  api_key?: string | null;
  model?: string;
  temperature?: number | null;
}

export interface LLMTestResult {
  provider: string;
  ok: boolean;
  model: string | null;
  error: string | null;
}
