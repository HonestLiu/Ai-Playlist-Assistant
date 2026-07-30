/** 数据层 hook：组件只消费这些，不直接碰 service。 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys, subsonicApi } from "@/services/subsonic";
import type { SubsonicConfigIn } from "@/types/api";

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: subsonicApi.health,
    retry: false,
    refetchInterval: 30_000,
  });
}

export function useSubsonicStatus() {
  return useQuery({
    queryKey: queryKeys.subsonicStatus,
    queryFn: subsonicApi.status,
    retry: false,
  });
}

export function useSubsonicConfig() {
  return useQuery({
    queryKey: queryKeys.subsonicConfig,
    queryFn: subsonicApi.getConfig,
    retry: false,
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: (body: SubsonicConfigIn) => subsonicApi.testConfig(body),
  });
}

export function useSaveConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: SubsonicConfigIn) => subsonicApi.saveConfig(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.subsonicConfig });
      void queryClient.invalidateQueries({ queryKey: queryKeys.subsonicStatus });
    },
  });
}

export function useResetConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: subsonicApi.resetConfig,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.subsonicConfig });
      void queryClient.invalidateQueries({ queryKey: queryKeys.subsonicStatus });
    },
  });
}
