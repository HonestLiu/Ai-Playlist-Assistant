import { Pause, Play } from "lucide-react";

import { Button } from "@/components/ui/button";
import { usePlayerStore } from "@/stores/player";
import type { PlayableTrack } from "@/types/player";

interface PlayButtonProps {
  track: PlayableTrack;
  queue: PlayableTrack[];
  index: number;
  className?: string;
  size?: "sm" | "icon" | "default";
}

/** 单首歌的播放/暂停按钮：若是当前曲目则切换播放状态，否则从它在队列中的位置开始播放。 */
export function PlayButton({ track, queue, index, className, size = "icon" }: PlayButtonProps) {
  const isCurrent = usePlayerStore((s) => s.queue[s.currentIndex]?.id === track.id);
  const isPlaying = usePlayerStore((s) => s.isPlaying);
  const setQueue = usePlayerStore((s) => s.setQueue);
  const toggle = usePlayerStore((s) => s.toggle);

  const active = isCurrent && isPlaying;
  return (
    <Button
      variant="ghost"
      size={size}
      className={className}
      aria-label={active ? "暂停" : "播放"}
      onClick={(e) => {
        e.stopPropagation();
        if (isCurrent) toggle();
        else setQueue(queue, index);
      }}
    >
      {active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
    </Button>
  );
}
