import { Check, ListMusic, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatDuration } from "@/lib/utils";
import type { RecommendationResult } from "@/types/ai";

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-accent px-2.5 py-0.5 text-xs text-accent-foreground">
      {children}
    </span>
  );
}

const LANG_LABEL: Record<string, string> = {
  ja: "日语",
  en: "英语",
  zh: "中文",
  ko: "韩语",
  fr: "法语",
};

export function RecommendationCard({
  result,
  saved,
  onSave,
}: {
  result: RecommendationResult;
  saved?: boolean;
  onSave?: () => void;
}) {
  const { intent } = result;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center gap-1.5">
        {intent.language?.map((l) => (
          <Chip key={`lang-${l}`}>{LANG_LABEL[l] ?? l}</Chip>
        ))}
        {intent.mood?.map((m) => (
          <Chip key={`mood-${m}`}>{m}</Chip>
        ))}
        {intent.genres?.map((g) => (
          <Chip key={`g-${g}`}>{g}</Chip>
        ))}
        {intent.decade != null && <Chip>{`${intent.decade}s`}</Chip>}
        {intent.energy && <Chip>{`节奏 ${intent.energy}`}</Chip>}
        <Chip>目标 {intent.target_size} 首</Chip>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <Sparkles className="h-3.5 w-3.5" /> 模型 {result.provider}
        </span>
        <span>召回候选 {result.total_candidates} 首</span>
        <span>命中 {result.songs.length} 首</span>
        <span>总时长 {formatDuration(result.total_duration)}</span>
      </div>

      <ol className="divide-y divide-border">
        {result.songs.map((song, i) => (
          <li key={song.id} className="flex items-start gap-3 py-2">
            <span className="mt-0.5 w-5 shrink-0 text-right text-xs text-muted-foreground">
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium">{song.title}</div>
              <div className="truncate text-xs text-muted-foreground">
                {song.artist_name ?? "未知艺术家"}
                {song.album_name ? ` · ${song.album_name}` : ""}
                {song.year ? ` · ${song.year}` : ""}
                {song.duration ? ` · ${formatDuration(song.duration)}` : ""}
              </div>
              {song.reason && (
                <div className="mt-0.5 text-xs text-muted-foreground/80">{song.reason}</div>
              )}
            </div>
          </li>
        ))}
      </ol>

      {onSave && (
        <div className="mt-4 flex justify-end">
          <Button size="sm" variant={saved ? "outline" : "default"} onClick={onSave} disabled={saved}>
            {saved ? (
              <>
                <Check className="mr-1.5 h-4 w-4" /> 已创建到 Subsonic
              </>
            ) : (
              <>
                <ListMusic className="mr-1.5 h-4 w-4" /> 创建到 Subsonic
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
