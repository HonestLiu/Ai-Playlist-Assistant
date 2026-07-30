/** 可播放曲目。前端播放器只关心这些字段，与本地 Song/后端 SongOut 解耦。 */

export interface PlayableTrack {
  id: string;
  title: string;
  artist_name: string | null;
  album_name: string | null;
  cover_art: string | null;
  duration: number | null;
}
