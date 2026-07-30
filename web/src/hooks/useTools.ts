/** 音乐库管理工具的数据层 hook。 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { toolsApi, toolsKeys } from "@/services/tools";

export function useDuplicates() {
  return useQuery({
    queryKey: toolsKeys.duplicates,
    queryFn: toolsApi.duplicates,
    retry: false,
  });
}

export function useDeleteDuplicates() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (song_ids: string[]) => toolsApi.deleteDuplicates(song_ids),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: toolsKeys.duplicates });
      void queryClient.invalidateQueries({ queryKey: toolsKeys.playlistDuplicates });
    },
  });
}

export function usePlaylistDuplicates() {
  return useQuery({
    queryKey: toolsKeys.playlistDuplicates,
    queryFn: toolsApi.playlistDuplicates,
    retry: false,
  });
}

export function useCleanPlaylist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (subsonic_id: string) => toolsApi.cleanPlaylist(subsonic_id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: toolsKeys.playlistDuplicates });
    },
  });
}

export function useMetadataGaps() {
  return useQuery({
    queryKey: toolsKeys.metadataGaps,
    queryFn: toolsApi.metadataGaps,
    retry: false,
  });
}
