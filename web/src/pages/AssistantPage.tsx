import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Check,
  Loader2,
  Send,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";

import { RecommendationCard } from "@/components/ai/RecommendationCard";
import { DailyMixCard } from "@/components/ai/DailyMixCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCreatePlaylist, usePreferences, useRecommend } from "@/hooks/useAI";
import { HttpError } from "@/services/http";
import type { RecommendationResult } from "@/types/ai";

interface Turn {
  query: string;
  result: RecommendationResult;
}

const STORAGE_KEY = "apa_assistant_history_v1";

/** 处理阶段（对应后端 recommend 的真实步骤）。 */
const STAGES = [
  "理解你的需求（解析意图）",
  "从曲库检索候选歌曲",
  "为你挑选最契合的歌曲",
  "整理歌单与推荐理由",
];

const EXAMPLES = [
  "适合晚上学习、节奏不要太快、以日语歌曲为主的歌单",
  "今天下雨了，来点慵懒的爵士",
  "写代码时听的纯音乐",
  "燃向的动漫歌曲",
];

function loadHistory(): Turn[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw) as unknown;
    return Array.isArray(data) ? (data as Turn[]) : [];
  } catch {
    return [];
  }
}

/** 用户消息气泡（右对齐） */
function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm leading-relaxed text-primary-foreground">
        {text}
      </div>
    </div>
  );
}

/** 助手头像 */
function AssistantAvatar() {
  return (
    <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
      <Sparkles className="h-4 w-4" />
    </div>
  );
}

/** 助手「进度」气泡：把单一「思考中」换成可感知的处理阶段。 */
function ProgressBubble({ stage }: { stage: number }) {
  return (
    <div className="flex items-start gap-2">
      <AssistantAvatar />
      <div className="rounded-2xl rounded-tl-sm border border-border bg-card px-4 py-3 text-sm">
        <div className="mb-2 text-muted-foreground">正在为你生成歌单…</div>
        <ul className="space-y-1.5">
          {STAGES.map((label, i) => {
            const n = i + 1;
            const done = stage > n;
            const active = stage === n;
            return (
              <li key={n} className="flex items-center gap-2">
                {done ? (
                  <Check className="h-4 w-4 shrink-0 text-emerald-500" />
                ) : active ? (
                  <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary" />
                ) : (
                  <span className="h-4 w-4 shrink-0 rounded-full border border-muted-foreground/40" />
                )}
                <span className={done || active ? "text-foreground" : "text-muted-foreground"}>
                  {label}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

/** 助手错误气泡（左对齐） */
function ErrorBubble({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2">
      <AssistantAvatar />
      <div className="rounded-2xl rounded-tl-sm border border-destructive/40 bg-destructive/5 px-4 py-2.5 text-sm text-destructive">
        出错了：{message}
      </div>
    </div>
  );
}

/** 创建歌单的结果横幅（成功/失败都明显提示）。 */
function FeedbackBanner({
  feedback,
  onClose,
}: {
  feedback: { type: "success" | "error"; message: string } | null;
  onClose: () => void;
}) {
  if (!feedback) return null;
  const isSuccess = feedback.type === "success";
  return (
    <div
      className={
        "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm " +
        (isSuccess
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-destructive/30 bg-destructive/5 text-destructive")
      }
    >
      {isSuccess ? (
        <Check className="h-4 w-4 shrink-0" />
      ) : (
        <AlertCircle className="h-4 w-4 shrink-0" />
      )}
      <span className="flex-1">{feedback.message}</span>
      <button
        type="button"
        onClick={onClose}
        className="shrink-0 opacity-60 transition-opacity hover:opacity-100"
        aria-label="关闭提示"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function AssistantPage() {
  const [turns, setTurns] = useState<Turn[]>(loadHistory);
  const [input, setInput] = useState("");
  const [createPlaylist, setCreatePlaylist] = useState(false);
  // 进行中的用户提问：发送后立即上屏，配合进度气泡形成对话流
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  // 当前处理阶段（1..4，0 表示空闲）
  const [stage, setStage] = useState(0);
  // 正在保存的对话下标（用于卡片按钮 loading）
  const [savingIndex, setSavingIndex] = useState<number | null>(null);
  // 创建结果横幅
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(
    null,
  );

  const recommend = useRecommend();
  const createMutation = useCreatePlaylist();
  const preferences = usePreferences();
  // 歌单标题前缀「AI · 」是否开启（默认开启），由用户在设置页决定
  const prefixEnabled = preferences.data?.playlist_title_prefix ?? true;
  const bottomRef = useRef<HTMLDivElement>(null);
  const stageTimers = useRef<number[]>([]);

  // 对话历史持久化：离开 Tab / 刷新后仍在
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(turns));
    } catch {
      /* 隐私模式等场景忽略写入失败 */
    }
  }, [turns]);

  // 卸载时清掉未触发的阶段定时器
  useEffect(() => {
    const timers = stageTimers.current;
    return () => timers.forEach((t) => clearTimeout(t));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, pendingQuery, recommend.isPending, recommend.isError, feedback]);

  /** 按当前歌单落盘到 Subsonic，返回歌单引用；失败抛错。title 为基础标题（不含前缀）。 */
  const createToSubsonic = async (
    query: string,
    result: RecommendationResult,
    title: string,
  ) => {
    const songIds = result.songs.map((s) => s.id);
    return createMutation.mutateAsync({ query, song_ids: songIds, name: title });
  };

  const run = async (query: string, withCreate: boolean) => {
    setPendingQuery(query);
    setStage(1);
    setFeedback(null);
    // 阶段随时间推进（贴合后端两步 LLM + SQL 的真实耗时分布）
    stageTimers.current = [
      window.setTimeout(() => setStage((s) => (s < 2 ? 2 : s)), 1200),
      window.setTimeout(() => setStage((s) => (s < 3 ? 3 : s)), 3200),
      window.setTimeout(() => setStage((s) => (s < 4 ? 4 : s)), 6200),
    ];
    try {
      let result = await recommend.mutateAsync({ query });
      // 生成后若勾选了「直接创建」，立即创建（不重新生成）
      if (withCreate && result.songs.length > 0) {
        try {
          const ref = await createToSubsonic(query, result, result.title ?? result.query);
          result = { ...result, playlist: ref };
          setFeedback({
            type: "success",
            message: `已创建到 Subsonic 歌单「${ref.name}」`,
          });
        } catch (e) {
          setFeedback({
            type: "error",
            message: e instanceof HttpError ? e.message : "创建歌单失败，请稍后再试",
          });
        }
      }
      setTurns((prev) => [...prev, { query, result }]);
    } catch {
      // 错误在 pendingQuery 区块显示，下次发送会被覆盖
    } finally {
      stageTimers.current.forEach((t) => clearTimeout(t));
      setPendingQuery(null);
      setStage(0);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || recommend.isPending) return;
    setInput("");
    void run(q, createPlaylist);
  };

  const handleSave = async (index: number, turn: Turn, title: string) => {
    if (savingIndex !== null) return;
    setSavingIndex(index);
    setFeedback(null);
    try {
      const ref = await createToSubsonic(turn.query, turn.result, title);
      setTurns((prev) =>
        prev.map((t, i) =>
          i === index ? { ...t, result: { ...t.result, playlist: ref } } : t,
        ),
      );
      setFeedback({
        type: "success",
        message: `已创建到 Subsonic 歌单「${ref.name}」`,
      });
    } catch (e) {
      setFeedback({
        type: "error",
        message: e instanceof HttpError ? e.message : "创建歌单失败，请稍后再试",
      });
    } finally {
      setSavingIndex(null);
    }
  };

  const clearHistory = () => {
    if (turns.length === 0) return;
    if (window.confirm("确定清除所有 AI 对话记录？此操作不可恢复。")) {
      setTurns([]);
      setFeedback(null);
    }
  };

  const errorMessage =
    recommend.isError && recommend.error
      ? (recommend.error as Error)?.message ?? "未知错误"
      : null;

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold">
            <Sparkles className="h-5 w-5 text-primary" /> AI 助手
          </h1>
          <p className="text-sm text-muted-foreground">
            用自然语言描述场景、心情或需求，让 AI 从你的曲库挑歌、生成歌单。
          </p>
        </div>
        {turns.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearHistory}
            className="shrink-0 text-muted-foreground"
          >
            <Trash2 className="mr-1.5 h-4 w-4" /> 清除对话
          </Button>
        )}
      </div>

      <DailyMixCard />

      {feedback && (
        <div className="mb-3">
          <FeedbackBanner feedback={feedback} onClose={() => setFeedback(null)} />
        </div>
      )}

      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto pr-1">
        {turns.length === 0 && !pendingQuery && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-muted-foreground">
              还没有对话。试试下面的例子，或直接输入你的需求。
            </CardContent>
          </Card>
        )}

        {turns.map((turn, i) => (
          <div key={i} className="space-y-3">
            <UserBubble text={turn.query} />
            <RecommendationCard
              result={turn.result}
              saved={!!turn.result.playlist}
              saving={savingIndex === i}
              prefixEnabled={prefixEnabled}
              onSave={(title) => void handleSave(i, turn, title)}
            />
          </div>
        ))}

        {pendingQuery && (
          <div className="space-y-3">
            <UserBubble text={pendingQuery} />
            {recommend.isPending && <ProgressBubble stage={stage} />}
            {errorMessage && <ErrorBubble message={errorMessage} />}
          </div>
        )}
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
