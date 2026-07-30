/** 播放相关的 URL 构造与类型转换。 */

import type { PlayableTrack } from "@/types/player";

/** 后端串流代理地址（Vite 代理到 :8000，浏览器侧同源）。 */
export function streamUrl(id: string): string {
  return `/api/v1/stream/${encodeURIComponent(id)}`;
}

/** 封面图代理地址；cover_art 为空返回 null（由组件回退占位）。 */
export function coverUrl(coverArt: string | null, size = 80): string | null {
  if (!coverArt) return null;
  return `/api/v1/subsonic/cover/${encodeURIComponent(coverArt)}?size=${size}`;
}

type SongLike = {
  id: string;
  title: string;
  artist_name?: string | null;
  album_name?: string | null;
  cover_art?: string | null;
  duration?: number | null;
};

/** 把任意含歌曲字段的对象规整成 PlayableTrack。 */
export function toTrack(s: SongLike): PlayableTrack {
  return {
    id: s.id,
    title: s.title,
    artist_name: s.artist_name ?? null,
    album_name: s.album_name ?? null,
    cover_art: s.cover_art ?? null,
    duration: s.duration ?? null,
  };
}
