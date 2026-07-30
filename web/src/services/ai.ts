/** AI 推荐 / 歌单 / LLM 配置接口调用。 */
import { request } from "@/services/http";
import type {
  CreatePlaylistBody,
  DailyMixRequest,
  DailyMixResult,
  LLMConfigIn,
  LLMConfigOut,
  LLMTestResult,
  Playlist,
  PlaylistDetail,
  PlaylistRef,
  PlaylistRenameIn,
  PlaylistSyncResult,
  PreferencesIn,
  PreferencesOut,
  RecommendationResult,
  SchedulerStatus,
  SchedulerTriggerResult,
} from "@/types/ai";

export interface RecommendVars {
  query: string;
  target_size?: number;
  create_playlist?: boolean;
  playlist_name?: string;
}

export const aiApi = {
  recommend: (body: RecommendVars) =>
    request<RecommendationResult>("/ai/recommend", { method: "POST", body }),
  // 把已生成的推荐结果直接落盘到 Subsonic（不重新跑 LLM）
  createPlaylist: (body: CreatePlaylistBody) =>
    request<PlaylistRef>("/ai/recommend/playlist", { method: "POST", body }),
  dailyMix: (body: DailyMixRequest = {}) =>
    request<DailyMixResult>("/ai/daily-mix", { method: "POST", body }),
  listPlaylists: () => request<Playlist[]>("/playlists"),
  syncPlaylists: () =>
    request<PlaylistSyncResult>("/playlists/sync", { method: "POST" }),
  getPlaylist: (id: number) => request<PlaylistDetail>(`/playlists/${id}`),
  deletePlaylist: (id: number) =>
    request<void>(`/playlists/${id}`, { method: "DELETE" }),
  renamePlaylist: (id: number, body: PlaylistRenameIn) =>
    request<Playlist>(`/playlists/${id}`, { method: "PATCH", body }),
  getLLMConfig: () => request<LLMConfigOut>("/settings/llm"),
  saveLLMConfig: (body: LLMConfigIn) =>
    request<LLMConfigOut>("/settings/llm", { method: "PUT", body }),
  testLLMConfig: (body: LLMConfigIn) =>
    request<LLMTestResult>("/settings/llm/test", { method: "POST", body }),
  getSchedulerStatus: () => request<SchedulerStatus>("/ai/scheduler/status"),
  triggerDailyMix: () =>
    request<SchedulerTriggerResult>("/ai/scheduler/trigger", { method: "POST" }),
  getPreferences: () => request<PreferencesOut>("/settings/preferences"),
  savePreferences: (body: PreferencesIn) =>
    request<PreferencesOut>("/settings/preferences", { method: "PUT", body }),
};

export const aiKeys = {
  playlists: ["playlists"] as const,
  playlist: (id: number) => ["playlists", id] as const,
  llmConfig: ["settings", "llm"] as const,
  preferences: ["settings", "preferences"] as const,
  dailyMix: ["daily-mix"] as const,
  schedulerStatus: ["scheduler", "status"] as const,
};
