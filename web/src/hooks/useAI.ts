/** AI 推荐 / 歌单相关的 react-query hooks。 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { aiApi, aiKeys, type RecommendVars } from "@/services/ai";
import type { CreatePlaylistBody } from "@/types/ai";

export function useRecommend() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: RecommendVars) => aiApi.recommend(vars),
    onSuccess: () => qc.invalidateQueries({ queryKey: aiKeys.playlists }),
  });
}

/** 把已生成的推荐结果直接创建为 Subsonic 歌单（不重新生成）。 */
export function useCreatePlaylist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreatePlaylistBody) => aiApi.createPlaylist(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: aiKeys.playlists }),
  });
}

export function useDailyMix() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: import("@/types/ai").DailyMixRequest = {}) =>
      aiApi.dailyMix(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: aiKeys.playlists });
      qc.invalidateQueries({ queryKey: aiKeys.dailyMix });
    },
  });
}

export function useRenamePlaylist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      aiApi.renamePlaylist(id, { name }),
    onSuccess: () => qc.invalidateQueries({ queryKey: aiKeys.playlists }),
  });
}

export function usePlaylists() {
  return useQuery({ queryKey: aiKeys.playlists, queryFn: aiApi.listPlaylists });
}

export function usePlaylist(id: number) {
  return useQuery({
    queryKey: aiKeys.playlist(id),
    queryFn: () => aiApi.getPlaylist(id),
    enabled: id > 0,
  });
}

export function useSyncPlaylists() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => aiApi.syncPlaylists(),
    onSuccess: () => qc.invalidateQueries({ queryKey: aiKeys.playlists }),
  });
}

export function useDeletePlaylist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => aiApi.deletePlaylist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: aiKeys.playlists }),
  });
}

export function useLLMConfig() {
  return useQuery({ queryKey: aiKeys.llmConfig, queryFn: aiApi.getLLMConfig });
}

export function useSchedulerStatus() {
  return useQuery({
    queryKey: aiKeys.schedulerStatus,
    queryFn: aiApi.getSchedulerStatus,
    refetchInterval: 15_000,
  });
}

export function useTriggerDailyMix() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => aiApi.triggerDailyMix(),
    onSuccess: () => {
      // 手动触发是异步后台任务，稍后轮询状态即可看到 last_run 更新
      setTimeout(() => qc.invalidateQueries({ queryKey: aiKeys.schedulerStatus }), 1500);
      qc.invalidateQueries({ queryKey: aiKeys.playlists });
    },
  });
}

export function useSaveLLMConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: import("@/types/ai").LLMConfigIn) => aiApi.saveLLMConfig(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: aiKeys.llmConfig }),
  });
}

export function useTestLLMConfig() {
  return useMutation({
    mutationFn: (body: import("@/types/ai").LLMConfigIn) => aiApi.testLLMConfig(body),
  });
}

export function usePreferences() {
  return useQuery({ queryKey: aiKeys.preferences, queryFn: aiApi.getPreferences });
}

export function useSavePreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: import("@/types/ai").PreferencesIn) => aiApi.savePreferences(body),
    onSuccess: (data) => qc.setQueryData(aiKeys.preferences, data),
  });
}
