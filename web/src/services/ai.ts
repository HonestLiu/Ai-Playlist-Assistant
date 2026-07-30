/** AI 推荐 / 歌单 / LLM 配置接口调用。 */
import { request } from "@/services/http";
import type {
  LLMConfigIn,
  LLMConfigOut,
  LLMTestResult,
  Playlist,
  PlaylistDetail,
  RecommendationResult,
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
  listPlaylists: () => request<Playlist[]>("/playlists"),
  getPlaylist: (id: number) => request<PlaylistDetail>(`/playlists/${id}`),
  deletePlaylist: (id: number) =>
    request<void>(`/playlists/${id}`, { method: "DELETE" }),
  getLLMConfig: () => request<LLMConfigOut>("/settings/llm"),
  saveLLMConfig: (body: LLMConfigIn) =>
    request<LLMConfigOut>("/settings/llm", { method: "PUT", body }),
  testLLMConfig: (body: LLMConfigIn) =>
    request<LLMTestResult>("/settings/llm/test", { method: "POST", body }),
};

export const aiKeys = {
  playlists: ["playlists"] as const,
  playlist: (id: number) => ["playlists", id] as const,
  llmConfig: ["settings", "llm"] as const,
};
