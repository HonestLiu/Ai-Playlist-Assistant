/** AI 推荐 / 歌单相关的 react-query hooks。 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { aiApi, aiKeys, type RecommendVars } from "@/services/ai";

export function useRecommend() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: RecommendVars) => aiApi.recommend(vars),
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
