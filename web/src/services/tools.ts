/** 音乐库管理工具接口调用。 */
import { request } from "@/services/http";

import type {
  DeleteResult,
  DuplicateReport,
  MetadataGapReport,
  PlaylistCleanResult,
  PlaylistDuplicateReport,
} from "@/types/tools";

export const toolsApi = {
  duplicates: () => request<DuplicateReport>("/tools/duplicates"),
  deleteDuplicates: (song_ids: string[]) =>
    request<DeleteResult>("/tools/duplicates/delete", {
      method: "POST",
      body: { song_ids },
    }),
  playlistDuplicates: () => request<PlaylistDuplicateReport>("/tools/playlists/duplicates"),
  cleanPlaylist: (subsonic_id: string) =>
    request<PlaylistCleanResult>("/tools/playlists/duplicates/clean", {
      method: "POST",
      body: { subsonic_id },
    }),
  metadataGaps: () => request<MetadataGapReport>("/tools/metadata-gaps"),
};

export const toolsKeys = {
  duplicates: ["tools", "duplicates"] as const,
  playlistDuplicates: ["tools", "playlists", "duplicates"] as const,
  metadataGaps: ["tools", "metadata-gaps"] as const,
};
