import { Link } from "react-router-dom";
import { RefreshCw, Sparkles } from "lucide-react";

import { useDailyMix } from "@/hooks/useAI";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RecommendationCard } from "@/components/ai/RecommendationCard";
import type { DailyMixResult } from "@/types/ai";

export function DailyMixCard() {
  const dailyMix = useDailyMix();
  const data = dailyMix.data as DailyMixResult | undefined;

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardContent className="py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="h-4 w-4 text-primary" /> 每日推荐
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              一键生成今天的专属歌单（按星期轮转主题，已生成则自动刷新）。
            </p>
          </div>
          <Button
            onClick={() => dailyMix.mutate({})}
            disabled={dailyMix.isPending}
            className="shrink-0"
          >
            {dailyMix.isPending ? (
              <RefreshCw className="mr-1.5 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-1.5 h-4 w-4" />
            )}
            {dailyMix.isPending ? "生成中…" : data ? "重新生成" : "生成今日推荐"}
          </Button>
        </div>

        {data?.playlist && (
          <div className="mt-3 rounded-md bg-background px-3 py-2 text-xs">
            {data.refreshed ? "已刷新" : "已生成"}今日推荐（
            {data.recommendation.songs.length} 首）
            {data.theme ? ` · 主题：${data.theme}` : ""} —
            <Link
              to={`/playlists/${data.playlist.id}`}
              className="ml-1 font-medium text-primary hover:underline"
            >
              查看歌单
            </Link>
          </div>
        )}

        {data && data.recommendation.songs.length > 0 && (
          <div className="mt-3">
            <RecommendationCard result={data.recommendation} saved={!!data.playlist} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
