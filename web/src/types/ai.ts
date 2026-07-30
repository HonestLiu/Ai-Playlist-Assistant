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

export interface DailyMixRequest {
  target_size?: number;
}

export interface DailyMixResult {
  query: string;
  theme: string;
  recommendation: RecommendationResult;
  playlist: PlaylistRef | null;
  refreshed: boolean;
  created: boolean;
}

export interface PlaylistRenameIn {
  name: string;
}

export interface SchedulerStatus {
  enabled: boolean;
  running: boolean;
  daily_mix_hour: number;
  daily_mix_minute: number;
  next_run: string | null;
  last_run: {
    ok: boolean;
    at: string;
    theme?: string;
    songs?: number;
    playlist?: string | null;
    action?: string;
    error?: string;
  } | null;
}

export interface SchedulerTriggerResult {
  triggered: boolean;
}

export interface PlaylistSyncResult {
  imported: number;
  updated: number;
  removed: number;
  total: number;
}

export interface RecommendationResult {
  query: string;
  intent: PlaylistIntent;
  provider: string;
  total_candidates: number;
  songs: RecommendedSong[];
  total_duration: number;
  title: string | null;
  playlist: PlaylistRef | null;
}

/** 用户偏好（如歌单标题是否带「AI · 」前缀）。 */
export interface PreferencesOut {
  playlist_title_prefix: boolean;
}

export interface PreferencesIn {
  playlist_title_prefix?: boolean;
}

/** 把已有推荐结果落盘到 Subsonic 歌单的请求体（不重新生成）。 */
export interface CreatePlaylistBody {
  query: string;
  song_ids: string[];
  name?: string;
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
