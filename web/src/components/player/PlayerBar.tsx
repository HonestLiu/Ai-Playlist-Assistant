import { useEffect, useRef } from "react";
import { Pause, Play, Repeat, Shuffle, SkipBack, SkipForward, Volume2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { coverUrl, streamUrl } from "@/lib/player";
import { formatDuration } from "@/lib/utils";
import { playHistoryApi } from "@/services/playHistory";
import { usePlayerStore } from "@/stores/player";

/** 全局播放条：持有唯一 <audio> 元素，订阅播放器 store 并驱动播放/进度/音量。 */
export function PlayerBar() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const recordedRef = useRef<string | null>(null);

  const queue = usePlayerStore((s) => s.queue);
  const currentIndex = usePlayerStore((s) => s.currentIndex);
  const isPlaying = usePlayerStore((s) => s.isPlaying);
  const currentTime = usePlayerStore((s) => s.currentTime);
  const duration = usePlayerStore((s) => s.duration);
  const volume = usePlayerStore((s) => s.volume);
  const repeat = usePlayerStore((s) => s.repeat);
  const shuffle = usePlayerStore((s) => s.shuffle);

  const current = queue[currentIndex];

  // 切歌：换源并（若处于播放态）自动播放
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !current) return;
    audio.src = streamUrl(current.id);
    audio.load();
    if (isPlaying) audio.play().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.id]);

  // 播放/暂停状态变化
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) audio.play().catch(() => {});
    else audio.pause();
  }, [isPlaying]);

  // 音量
  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
  }, [volume]);

  const handlePlay = () => {
    const audio = audioRef.current;
    if (current && recordedRef.current !== current.id) {
      recordedRef.current = current.id;
      playHistoryApi.record(current.id).catch(() => {});
      usePlayerStore.getState().setCurrentTime(0);
    }
    if (audio) usePlayerStore.getState().setDuration(audio.duration || 0);
  };

  const handleEnded = () => {
    const store = usePlayerStore.getState();
    if (store.repeat === "one") {
      const audio = audioRef.current;
      if (audio) {
        audio.currentTime = 0;
        audio.play().catch(() => {});
      }
    } else {
      store.onEnded();
    }
  };

  const cover = coverUrl(current?.cover_art ?? null, 48);

  return (
    <>
      <audio
        ref={audioRef}
        onPlay={handlePlay}
        onTimeUpdate={(e) => usePlayerStore.getState().setCurrentTime(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => usePlayerStore.getState().setDuration(e.currentTarget.duration || 0)}
        onEnded={handleEnded}
      />
      {current && (
        <div className="flex shrink-0 items-center gap-4 border-t border-border bg-card px-4 py-3">
          {/* 左：封面 + 曲目信息 */}
          <div className="flex min-w-0 flex-1 items-center gap-3">
            {cover ? (
              <img src={cover} alt={current.title} className="h-11 w-11 shrink-0 rounded object-cover" />
            ) : (
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded bg-accent text-muted-foreground">
                ♪
              </div>
            )}
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{current.title}</div>
              <div className="truncate text-xs text-muted-foreground">
                {current.artist_name ?? "未知艺术家"}
                {current.album_name ? ` · ${current.album_name}` : ""}
              </div>
            </div>
          </div>

          {/* 中：控制 + 进度 */}
          <div className="flex max-w-xl flex-1 flex-col items-center gap-1.5">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => usePlayerStore.getState().toggleShuffle()}
                className={shuffle ? "text-primary" : ""}
                aria-label="随机播放"
              >
                <Shuffle className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => usePlayerStore.getState().prev()}
                aria-label="上一首"
              >
                <SkipBack className="h-4 w-4" />
              </Button>
              <Button
                variant="default"
                size="icon"
                onClick={() => usePlayerStore.getState().toggle()}
                aria-label={isPlaying ? "暂停" : "播放"}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => usePlayerStore.getState().next()}
                aria-label="下一首"
              >
                <SkipForward className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => usePlayerStore.getState().cycleRepeat()}
                className={repeat !== "off" ? "text-primary" : ""}
                aria-label="循环模式"
              >
                <Repeat className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex w-full items-center gap-2">
              <span className="w-10 text-right text-xs tabular-nums text-muted-foreground">
                {formatDuration(currentTime)}
              </span>
              <input
                type="range"
                min={0}
                max={duration || 0}
                step={1}
                value={Math.min(currentTime, duration || 0)}
                onChange={(e) => {
                  const t = Number(e.target.value);
                  if (audioRef.current) audioRef.current.currentTime = t;
                  usePlayerStore.getState().setCurrentTime(t);
                }}
                className="h-1 flex-1 cursor-pointer accent-primary"
                aria-label="播放进度"
              />
              <span className="w-10 text-xs tabular-nums text-muted-foreground">
                {formatDuration(duration)}
              </span>
            </div>
          </div>

          {/* 右：音量 */}
          <div className="flex flex-1 items-center justify-end gap-2">
            <Volume2 className="h-4 w-4 text-muted-foreground" />
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={volume}
              onChange={(e) => usePlayerStore.getState().setVolume(Number(e.target.value))}
              className="h-1 w-24 cursor-pointer accent-primary"
              aria-label="音量"
            />
          </div>
        </div>
      )}
    </>
  );
}
