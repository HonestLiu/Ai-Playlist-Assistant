import { Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { RecommendationCard } from "@/components/ai/RecommendationCard";
import { DailyMixCard } from "@/components/ai/DailyMixCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useRecommend } from "@/hooks/useAI";
import type { RecommendationResult } from "@/types/ai";

interface Turn {
  query: string;
  result: RecommendationResult;
}

const EXAMPLES = [
  "适合晚上学习、节奏不要太快、以日语歌曲为主的歌单",
  "今天下雨了，来点慵懒的爵士",
  "写代码时听的纯音乐",
  "燃向的动漫歌曲",
];

export function AssistantPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [createPlaylist, setCreatePlaylist] = useState(false);
  const recommend = useRecommend();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, recommend.isPending]);

  const run = async (query: string, withCreate: boolean) => {
    const result = await recommend.mutateAsync({
      query,
      create_playlist: withCreate,
    });
    setTurns((prev) => [...prev, { query, result }]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || recommend.isPending) return;
    setInput("");
    void run(q, createPlaylist);
  };

  const handleSave = async (turn: Turn) => {
    const result = await recommend.mutateAsync({
      query: turn.query,
      create_playlist: true,
    });
    setTurns((prev) =>
      prev.map((t) => (t.query === turn.query ? { ...t, result } : t)),
    );
  };

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <div className="mb-4">
        <h1 className="flex items-center gap-2 text-xl font-semibold">
          <Sparkles className="h-5 w-5 text-primary" /> AI 助手
        </h1>
        <p className="text-sm text-muted-foreground">
          用自然语言描述场景、心情或需求，让 AI 从你的曲库挑歌、生成歌单。
        </p>
      </div>

      <DailyMixCard />

      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto pr-1">
        {turns.length === 0 && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-muted-foreground">
              还没有对话。试试下面的例子，或直接输入你的需求。
            </CardContent>
          </Card>
        )}

        {turns.map((turn, i) => (
          <div key={i} className="space-y-2">
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2 text-sm text-primary-foreground">
                {turn.query}
              </div>
            </div>
            <RecommendationCard
              result={turn.result}
              saved={!!turn.result.playlist}
              onSave={() => void handleSave(turn)}
            />
          </div>
        ))}

        {recommend.isPending && (
          <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
            正在思考并挑选歌曲…
          </div>
        )}

        {recommend.isError && (
          <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
            出错了：{(recommend.error as Error)?.message ?? "未知错误"}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="mt-4 space-y-3">
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              disabled={recommend.isPending}
              onClick={() => void run(ex, createPlaylist)}
              className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
            >
              {ex}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <label className="flex shrink-0 cursor-pointer items-center gap-1.5 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={createPlaylist}
              onChange={(e) => setCreatePlaylist(e.target.checked)}
              className="accent-primary"
            />
            直接创建到 Subsonic
          </label>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="例如：给我一个适合跑步的燃向歌单"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
          />
          <Button type="submit" disabled={!input.trim() || recommend.isPending}>
            <Send className="mr-1.5 h-4 w-4" /> 生成
          </Button>
        </form>
      </div>
    </div>
  );
}
