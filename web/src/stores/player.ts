/** 全局播放器状态（zustand）。单个 <audio> 元素由 PlayerBar 持有，状态集中在这里。 */

import { create } from "zustand";

import type { PlayableTrack } from "@/types/player";

export type RepeatMode = "off" | "all" | "one";

interface PlayerState {
  queue: PlayableTrack[];
  currentIndex: number;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  repeat: RepeatMode;
  shuffle: boolean;

  setQueue: (tracks: PlayableTrack[], startIndex?: number) => void;
  toggle: () => void;
  next: () => void;
  prev: () => void;
  seek: (time: number) => void;
  setVolume: (v: number) => void;
  setCurrentTime: (t: number) => void;
  setDuration: (d: number) => void;
  cycleRepeat: () => void;
  toggleShuffle: () => void;
  onEnded: () => void;
}

function randomOther(current: number, n: number): number {
  if (n <= 1) return 0;
  let idx = current;
  while (idx === current) idx = Math.floor(Math.random() * n);
  return idx;
}

export const usePlayerStore = create<PlayerState>((set) => ({
  queue: [],
  currentIndex: -1,
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  volume: 0.9,
  repeat: "off",
  shuffle: false,

  setQueue: (tracks, startIndex = 0) =>
    set({
      queue: tracks,
      currentIndex: tracks.length ? startIndex : -1,
      isPlaying: tracks.length > 0,
      currentTime: 0,
    }),

  toggle: () => set((s) => ({ isPlaying: !s.isPlaying })),

  next: () =>
    set((s) => {
      const n = s.queue.length;
      if (n === 0) return { currentIndex: -1 };
      let idx = s.shuffle ? randomOther(s.currentIndex, n) : s.currentIndex + 1;
      if (idx >= n) idx = s.repeat === "all" ? 0 : n - 1;
      if (idx < 0) idx = 0;
      return { currentIndex: idx, currentTime: 0 };
    }),

  prev: () =>
    set((s) => {
      const n = s.queue.length;
      if (n === 0) return { currentIndex: -1 };
      // 播放超过 3 秒时，上一首先回到本曲开头
      if (s.currentTime > 3) return { currentTime: 0 };
      let idx = s.shuffle ? randomOther(s.currentIndex, n) : s.currentIndex - 1;
      if (idx < 0) idx = s.repeat === "all" ? n - 1 : 0;
      return { currentIndex: idx, currentTime: 0 };
    }),

  seek: (time) => set({ currentTime: time }),
  setVolume: (v) => set({ volume: v }),
  setCurrentTime: (t) => set({ currentTime: t }),
  setDuration: (d) => set({ duration: d }),

  cycleRepeat: () =>
    set((s) => ({
      repeat: s.repeat === "off" ? "all" : s.repeat === "all" ? "one" : "off",
    })),
  toggleShuffle: () => set((s) => ({ shuffle: !s.shuffle })),

  onEnded: () =>
    set((s) => {
      const n = s.queue.length;
      if (n === 0 || s.repeat === "one") return {};
      let idx = s.shuffle ? randomOther(s.currentIndex, n) : s.currentIndex + 1;
      if (idx >= n) {
        if (s.repeat === "all") idx = 0;
        else return { isPlaying: false };
      }
      return { currentIndex: idx, currentTime: 0, isPlaying: true };
    }),
}));
