/** 播放历史上报（驱动 Daily Mix 个性化）。 */
import { request } from "@/services/http";

export const playHistoryApi = {
  record: (songId: string) =>
    request<{ ok: boolean }>("/play-history", {
      method: "POST",
      body: { song_id: songId },
    }),
};
