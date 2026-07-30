import {
  ArrowLeft,
  ArrowRight,
  Check,
  Disc3,
  Loader2,
  PartyPopper,
  RefreshCw,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input, Label, Toggle } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import { useLLMConfig, useSaveLLMConfig, useTestLLMConfig } from "@/hooks/useAI";
import {
  useBootstrap,
  useCompleteSetup,
  useSession,
  useSetupStatus,
} from "@/hooks/useAuth";
import { useSyncStatus, useTriggerSync } from "@/hooks/useLibrary";
import { useSaveConfig, useSubsonicConfig, useTestConnection } from "@/hooks/useSubsonic";
import { HttpError } from "@/services/http";
import { cn } from "@/lib/utils";
import type { ConnectionStatus, SubsonicConfigIn } from "@/types/api";
import type { LLMConfigIn, LLMTestResult } from "@/types/ai";
import type { SyncState } from "@/types/library";

const STEPS = ["管理员账号", "音乐服务器", "AI 模型", "同步曲库"] as const;

export function SetupPage() {
  const session = useSession();
  const navigate = useNavigate();
  const needsBootstrap = session.data?.needs_bootstrap ?? false;
  const authenticated = session.data?.authenticated ?? false;

  // 已有账号时跳过第一步；引导本身也可以从设置页重新进入
  const [step, setStep] = useState(0);
  useEffect(() => {
    if (session.data && !needsBootstrap) setStep((prev) => (prev === 0 ? 1 : prev));
  }, [session.data, needsBootstrap]);

  if (session.isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }
  // 已完成引导且已登录，没必要再看向导
  if (session.data?.onboarding_completed && authenticated) {
    return <Navigate to="/" replace />;
  }
  // 已有账号但没登录：先去登录，否则后面每一步都会 401
  if (!needsBootstrap && !authenticated) return <Navigate to="/login" replace />;

  return (
    <div className="mx-auto flex min-h-full max-w-2xl flex-col justify-center gap-6 px-4 py-10">
      <div className="flex flex-col items-center gap-2 text-center">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Disc3 className="h-6 w-6" />
        </span>
        <h1 className="text-lg font-medium">欢迎使用歌单助手</h1>
        <p className="text-sm text-muted-foreground">
          几步配置就能开始：创建账号、连接音乐服务器、接入 AI，然后同步曲库
        </p>
      </div>

      <StepIndicator current={step} />

      {step === 0 ? (
        <AccountStep onDone={() => setStep(1)} />
      ) : step === 1 ? (
        <SubsonicStep onBack={needsBootstrap ? () => setStep(0) : undefined} onDone={() => setStep(2)} />
      ) : step === 2 ? (
        <LLMStep onBack={() => setStep(1)} onDone={() => setStep(3)} />
      ) : (
        <FinishStep onBack={() => setStep(2)} onDone={() => navigate("/", { replace: true })} />
      )}
    </div>
  );
}

function StepIndicator({ current }: { current: number }) {
  return (
    <ol className="flex items-center justify-between gap-2">
      {STEPS.map((label, index) => {
        const done = index < current;
        const active = index === current;
        return (
          <li key={label} className="flex flex-1 items-center gap-2">
            <span
              className={cn(
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-medium transition-colors",
                done
                  ? "bg-[var(--success)] text-white"
                  : active
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground",
              )}
            >
              {done ? <Check className="h-3.5 w-3.5" /> : index + 1}
            </span>
            <span
              className={cn(
                "truncate text-xs",
                active ? "font-medium text-foreground" : "text-muted-foreground",
              )}
            >
              {label}
            </span>
            {index < STEPS.length - 1 ? (
              <span className="hidden h-px flex-1 bg-border sm:block" />
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

// ---------------------------------------------------------------- ① 账号
function AccountStep({ onDone }: { onDone: () => void }) {
  const bootstrap = useBootstrap();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mismatch = confirm.length > 0 && password !== confirm;
  const valid = username.trim().length >= 2 && password.length >= 6 && !mismatch;

  const submit = async () => {
    setError(null);
    try {
      await bootstrap.mutateAsync({ username: username.trim(), password });
      onDone();
    } catch (err) {
      setError(err instanceof HttpError ? err.message : "创建失败，请重试");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>创建管理员账号</CardTitle>
        <CardDescription>
          用于登录本应用，与音乐服务器的账号无关。密码至少 6 位。
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="setup-username">用户名</Label>
          <Input
            id="setup-username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="setup-password">密码</Label>
            <Input
              id="setup-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="setup-confirm">确认密码</Label>
            <Input
              id="setup-confirm"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
        </div>
        {mismatch ? <p className="text-sm text-destructive">两次输入的密码不一致</p> : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </CardContent>
      <CardFooter className="justify-end">
        <Button disabled={!valid || bootstrap.isPending} onClick={() => void submit()}>
          {bootstrap.isPending ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : null}
          创建并继续
          <ArrowRight className="ml-1.5 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}

// ---------------------------------------------------------------- ② Subsonic
function SubsonicStep({ onBack, onDone }: { onBack?: () => void; onDone: () => void }) {
  const config = useSubsonicConfig();
  const test = useTestConnection();
  const save = useSaveConfig();

  const [form, setForm] = useState<SubsonicConfigIn>({
    url: "",
    username: "",
    password: "",
    legacy_auth: false,
    verify_ssl: true,
  });
  const [result, setResult] = useState<ConnectionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!config.data) return;
    setForm((prev) => ({
      ...prev,
      url: prev.url || config.data.url,
      username: prev.username || config.data.username,
      legacy_auth: config.data.legacy_auth,
      verify_ssl: config.data.verify_ssl,
    }));
  }, [config.data]);

  const update = <K extends keyof SubsonicConfigIn>(key: K, value: SubsonicConfigIn[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setResult(null);
    setError(null);
  };

  const canSubmit = Boolean(form.url && form.username);

  const submit = async () => {
    setError(null);
    try {
      await save.mutateAsync(form);
      onDone();
    } catch (err) {
      setError(err instanceof HttpError ? err.message : "保存失败");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>连接音乐服务器</CardTitle>
        <CardDescription>
          支持 Navidrome、Airsonic 等兼容 Subsonic API 的服务端，填根地址即可
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="setup-url">服务器地址</Label>
          <Input
            id="setup-url"
            placeholder="http://192.168.1.10:4533"
            value={form.url}
            onChange={(e) => update("url", e.target.value)}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="setup-sub-user">用户名</Label>
            <Input
              id="setup-sub-user"
              autoComplete="off"
              value={form.username}
              onChange={(e) => update("username", e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="setup-sub-pass">密码</Label>
            <Input
              id="setup-sub-pass"
              type="password"
              autoComplete="off"
              placeholder={config.data?.has_password ? "留空沿用已保存密码" : ""}
              value={form.password ?? ""}
              onChange={(e) => update("password", e.target.value)}
            />
          </div>
        </div>
        <Toggle
          label="兼容旧版认证"
          description="老服务器不支持 salt+token 时才需要开启"
          checked={form.legacy_auth}
          onCheckedChange={(v) => update("legacy_auth", v)}
        />
        <Toggle
          label="校验 HTTPS 证书"
          description="自签名证书的自建服务需要关闭"
          checked={form.verify_ssl}
          onCheckedChange={(v) => update("verify_ssl", v)}
        />

        {result ? (
          <div className="rounded-md border border-border bg-muted px-3 py-3 text-sm">
            {result.connected ? (
              <div className="flex flex-col gap-1">
                <StatusBadge tone="success" className="self-start">
                  连接成功
                </StatusBadge>
                <span className="text-muted-foreground">
                  {result.server?.server_type} {result.server?.server_version} ·{" "}
                  {result.latency_ms} ms
                </span>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                <StatusBadge tone="danger" className="self-start">
                  连接失败
                </StatusBadge>
                <span className="text-muted-foreground">{result.error_message}</span>
              </div>
            )}
          </div>
        ) : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </CardContent>
      <CardFooter className="justify-between">
        {onBack ? (
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="mr-1.5 h-4 w-4" />
            上一步
          </Button>
        ) : (
          <span />
        )}
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={!canSubmit || test.isPending}
            onClick={async () => setResult(await test.mutateAsync(form))}
          >
            {test.isPending ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : null}
            测试连接
          </Button>
          <Button disabled={!canSubmit || save.isPending} onClick={() => void submit()}>
            保存并继续
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

// ---------------------------------------------------------------- ③ LLM
function LLMStep({ onBack, onDone }: { onBack: () => void; onDone: () => void }) {
  const config = useLLMConfig();
  const save = useSaveLLMConfig();
  const test = useTestLLMConfig();

  const [provider, setProvider] = useState("openai");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [result, setResult] = useState<LLMTestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!config.data) return;
    setProvider(config.data.provider);
    setBaseUrl((prev) => prev || config.data.base_url);
    setModel((prev) => prev || config.data.model);
  }, [config.data]);

  const body = useMemo<LLMConfigIn>(
    () => ({
      provider,
      base_url: baseUrl || undefined,
      api_key: apiKey || null,
      model: model || undefined,
    }),
    [provider, baseUrl, apiKey, model],
  );

  // mock 不需要 key；真实 provider 要么这次填了，要么之前存过
  const ready = provider === "mock" || Boolean(apiKey) || Boolean(config.data?.has_api_key);

  const submit = async () => {
    setError(null);
    try {
      await save.mutateAsync(body);
      onDone();
    } catch (err) {
      setError(err instanceof HttpError ? err.message : "保存失败");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>接入 AI 模型</CardTitle>
        <CardDescription>
          用于理解「想听点安静的下午茶音乐」这类需求。任何 OpenAI 兼容接口都可以
          （DeepSeek / OpenRouter / 硅基流动 / Ollama 等）
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="setup-provider">Provider</Label>
            <select
              id="setup-provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="h-9 rounded-md border border-border bg-background px-3 text-sm outline-none focus:border-primary"
            >
              <option value="openai">OpenAI 兼容</option>
              <option value="mock">Mock（先跳过，本地假数据）</option>
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="setup-model">模型名</Label>
            <Input
              id="setup-model"
              placeholder="deepseek-chat"
              disabled={provider === "mock"}
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="setup-baseurl">Base URL</Label>
          <Input
            id="setup-baseurl"
            placeholder="https://api.deepseek.com/v1"
            disabled={provider === "mock"}
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="setup-apikey">API Key</Label>
          <Input
            id="setup-apikey"
            type="password"
            autoComplete="off"
            disabled={provider === "mock"}
            placeholder={config.data?.has_api_key ? "留空沿用已保存的 key" : "sk-..."}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </div>

        {result ? (
          <div className="rounded-md border border-border bg-muted px-3 py-3 text-sm">
            {result.ok ? (
              <div className="flex flex-col gap-1">
                <StatusBadge tone="success" className="self-start">
                  调用成功
                </StatusBadge>
                <span className="text-muted-foreground">{result.model}</span>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                <StatusBadge tone="danger" className="self-start">
                  调用失败
                </StatusBadge>
                <span className="text-muted-foreground">{result.error}</span>
              </div>
            )}
          </div>
        ) : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </CardContent>
      <CardFooter className="justify-between">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          上一步
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={test.isPending || !ready}
            onClick={async () => setResult(await test.mutateAsync(body))}
          >
            {test.isPending ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : null}
            测试
          </Button>
          <Button disabled={save.isPending || !ready} onClick={() => void submit()}>
            保存并继续
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

// ---------------------------------------------------------------- ④ 同步 + 完成
function FinishStep({ onBack, onDone }: { onBack: () => void; onDone: () => void }) {
  const status = useSetupStatus(false);
  const syncStatus = useSyncStatus();
  const triggerSync = useTriggerSync();
  const complete = useCompleteSetup();

  const running = syncStatus.data?.status === "running" || syncStatus.data?.status === "queued";
  const songCount = status.data?.song_count ?? 0;
  const syncData = syncStatus.data;
  const syncView = syncData && syncData.status !== "never" ? (syncData as SyncState) : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>同步曲库</CardTitle>
        <CardDescription>
          把服务器上的艺术家、专辑、歌曲索引到本地，AI 才能据此选歌。曲库大时首次同步需要几十秒。
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-2 text-sm">
          <SummaryRow label="管理员账号" ok={status.data?.account_ready} />
          <SummaryRow
            label="音乐服务器"
            ok={status.data?.subsonic_configured}
            hint={status.data?.subsonic_configured ? undefined : "未配置"}
          />
          <SummaryRow
            label="AI 模型"
            ok={status.data?.llm_configured}
            hint={status.data?.llm_provider === "mock" ? "Mock 模式" : undefined}
          />
          <SummaryRow
            label="本地曲库"
            ok={songCount > 0}
            hint={songCount > 0 ? `${songCount} 首` : "尚未同步"}
          />
        </div>

        {syncView ? (
          <div className="rounded-md border border-border bg-muted px-3 py-3 text-sm">
            <div className="flex items-center gap-2">
              <StatusBadge
                tone={
                  syncView.status === "success"
                    ? "success"
                    : syncView.status === "failed"
                      ? "danger"
                      : "warning"
                }
              >
                {syncView.status}
              </StatusBadge>
              <span className="text-muted-foreground">
                艺术家 {syncView.artists_synced} · 专辑 {syncView.albums_synced} · 歌曲{" "}
                {syncView.songs_synced}
              </span>
            </div>
            {syncView.error ? (
              <p className="mt-1 text-destructive">{syncView.error}</p>
            ) : null}
          </div>
        ) : null}
      </CardContent>
      <CardFooter className="justify-between">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          上一步
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={running || triggerSync.isPending || !status.data?.subsonic_configured}
            onClick={() => triggerSync.mutate()}
          >
            {running || triggerSync.isPending ? (
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-1.5 h-4 w-4" />
            )}
            {running ? "同步中…" : "立即同步"}
          </Button>
          <Button
            disabled={complete.isPending}
            onClick={async () => {
              await complete.mutateAsync();
              onDone();
            }}
          >
            <PartyPopper className="mr-1.5 h-4 w-4" />
            完成，开始使用
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

function SummaryRow({
  label,
  ok,
  hint,
}: {
  label: string;
  ok?: boolean;
  hint?: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
      <span>{label}</span>
      <span className="flex items-center gap-2">
        {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
        <StatusBadge tone={ok ? "success" : "warning"}>{ok ? "已就绪" : "待完成"}</StatusBadge>
      </span>
    </div>
  );
}
