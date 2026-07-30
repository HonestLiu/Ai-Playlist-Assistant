/** 音乐库数据层 hook。 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { libraryApi, libraryKeys } from "@/services/library";
import type { ListQuery } from "@/types/library";

export function useSyncStatus() {
  return useQuery({
    queryKey: libraryKeys.syncStatus,
    queryFn: libraryApi.syncStatus,
    retry: false,
    refetchInterval: 5_000,
  });
}

export function useTriggerSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: libraryApi.sync,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: libraryKeys.syncStatus });
      void queryClient.invalidateQueries({ queryKey: ["artists"] });
      void queryClient.invalidateQueries({ queryKey: ["albums"] });
      void queryClient.invalidateQueries({ queryKey: ["songs"] });
    },
  });
}

export function useArtists(params: ListQuery = {}) {
  return useQuery({
    queryKey: libraryKeys.artists(params),
    queryFn: () => libraryApi.listArtists(params),
    placeholderData: (prev) => prev,
  });
}

export function useArtist(id: string) {
  return useQuery({
    queryKey: libraryKeys.artist(id),
    queryFn: () => libraryApi.getArtist(id),
    enabled: Boolean(id),
  });
}

export function useAlbums(params: ListQuery = {}) {
  return useQuery({
    queryKey: libraryKeys.albums(params),
    queryFn: () => libraryApi.listAlbums(params),
    placeholderData: (prev) => prev,
  });
}

export function useAlbum(id: string) {
  return useQuery({
    queryKey: libraryKeys.album(id),
    queryFn: () => libraryApi.getAlbum(id),
    enabled: Boolean(id),
  });
}

export function useSongs(params: ListQuery = {}) {
  return useQuery({
    queryKey: libraryKeys.songs(params),
    queryFn: () => libraryApi.listSongs(params),
    placeholderData: (prev) => prev,
  });
}

export function useSong(id: string) {
  return useQuery({
    queryKey: libraryKeys.song(id),
    queryFn: () => libraryApi.getSong(id),
    enabled: Boolean(id),
  });
}
