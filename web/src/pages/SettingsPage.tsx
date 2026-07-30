import { KeyRound, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

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
import {
  useResetConfig,
  useSaveConfig,
  useSubsonicConfig,
  useTestConnection,
} from "@/hooks/useSubsonic";
import { useLLMConfig, usePreferences, useSaveLLMConfig, useSavePreferences, useTestLLMConfig } from "@/hooks/useAI";
import { useChangePassword, useSession } from "@/hooks/useAuth";
import { HttpError } from "@/services/http";
import type { ConnectionStatus, SubsonicConfigIn } from "@/types/api";
import type { LLMConfigIn, LLMTestResult } from "@/types/ai";

const emptyForm: SubsonicConfigIn = {
  url: "",
  username: "",
  password: "",
  legacy_auth: false,
  verify_ssl: true,
};

export function SettingsPage() {
  const config = useSubsonicConfig();
  const testConnection = useTestConnection();
  const saveConfig = useSaveConfig();
  const resetConfig = useResetConfig();

  const [form, setForm] = useState<SubsonicConfigIn>(emptyForm);
  const [result, setResult] = useState<ConnectionStatus | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!config.data) return;
    setForm({
      url: config.data.url,
      username: config.data.username,
      password: "",
      legacy_auth: config.data.legacy_auth,
      verify_ssl: config.data.verify_ssl,
    });
  }, [config.data]);

  const update = <K extends keyof SubsonicConfigIn>(key: K, value: SubsonicConfigIn[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setResult(null);
    setSaved(false);
  };

  const handleTest = async () => {
    setSaved(false);
    const status = await testConnection.mutateAsync(form);
    setResult(status);
  };

  const handleSave = async () => {
    await saveConfig.mutateAsync(form);
    setSaved(true);
  };

  const handleReset = async () => {
    await resetConfig.mutateAsync();
    setResult(null);
    setSaved(false);
  };

  const busy = testConnection.isPending || saveConfig.isPending || resetConfig.isPending;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="text-xl font-medium">设置</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          配置 Subsonic 服务器连接。网页保存的值会覆盖 .env 中的默认配置。
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>Subsonic 服务器</CardTitle>
              <CardDescription>
                支持 Navidrome、Airsonic 等兼容 Subsonic API 1.16.1 的服务端
              </CardDescription>
            </div>
            <StatusBadge tone={config.data?.source === "runtime" ? "success" : "muted"}>
              {config.data?.source === "runtime" ? "网页配置" : "来自 .env"}
            </StatusBadge>
          </div>
        </CardHeader>

        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="url">服务器地址</Label>
            <Input
              id="url"
              placeholder="https://music.example.com"
              value={form.url}
              onChange={(e) => update("url", e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              填根地址即可，客户端会自动补 /rest 路径
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                autoComplete="username"
                value={form.username}
                onChange={(e) => update("username", e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder={config.data?.has_password ? "留空则沿用已保存密码" : ""}
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
                    {result.server?.server_type} {result.server?.server_version} · API{" "}
                    {result.server?.version} · {result.latency_ms} ms
                  </span>
                </div>
              ) : (
                <div className="flex flex-col gap-1">
                  <StatusBadge tone="danger" className="self-start">
                    连接失败
                  </StatusBadge>
                  <span className="text-muted-foreground">{result.error_message}</span>
                  <span className="font-mono text-xs text-muted-foreground opacity-70">
                    {result.error_code}
                  </span>
                </div>
              )}
            </div>
          ) : null}

          {saved ? (
            <p className="text-sm text-[var(--success)]">配置已保存</p>
          ) : null}
        </CardContent>

        <CardFooter className="justify-between">
          <Button
            variant="ghost"
            size="sm"
            disabled={busy || config.data?.source !== "runtime"}
            onClick={() => void handleReset()}
          >
            恢复为 .env
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" disabled={busy} onClick={() => void handleTest()}>
              {testConnection.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              测试连接
            </Button>
            <Button disabled={busy || !form.url || !form.username} onClick={() => void handleSave()}>
              保存
            </Button>
          </div>
        </CardFooter>
      </Card>

      <LLMSettingsCard />
      <PreferencesCard />
      <AccountCard />
    </div>
  );
}

function PreferencesCard() {
  const prefs = usePreferences();
  const save = useSavePreferences();
  const [prefixEnabled, setPrefixEnabled] = useState(true);

  useEffect(() => {
    if (prefs.data) setPrefixEnabled(prefs.data.playlist_title_prefix);
  }, [prefs.data]);

  const toggle = async (value: boolean) => {
    setPrefixEnabled(value);
    try {
      await save.mutateAsync({ playlist_title_prefix: value });
    } catch {
      setPrefixEnabled(!value); // 保存失败则回滚
    }
  };

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>偏好</CardTitle>
          <CardDescription>歌单标题与界面相关的小设置</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Toggle
          label="歌单标题保留「AI · 」前缀"
          description="开启时，AI 生成的歌单会命名为「AI · 标题」；关闭后直接使用 AI 生成的标题（如「深夜书房 BGM」）"
          checked={prefixEnabled}
          onCheckedChange={(v) => void toggle(v)}
        />
      </CardContent>
    </Card>
  );
}

function AccountCard() {
  const session = useSession();
  const changePassword = useChangePassword();

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  if (!session.data?.auth_enabled) return null;

  const mismatch = confirm.length > 0 && next !== confirm;
  const valid = current.length > 0 && next.length >= 6 && !mismatch;

  const submit = async () => {
    setError(null);
    setDone(false);
    try {
      await changePassword.mutateAsync({ current_password: current, new_password: next });
      setCurrent("");
      setNext("");
      setConfirm("");
      setDone(true);
    } catch (err) {
      setError(err instanceof HttpError ? err.message : "修改失败");
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>账号</CardTitle>
            <CardDescription>
              当前登录：{session.data.user?.username ?? "-"}。修改密码后其它设备会被强制登出。
            </CardDescription>
          </div>
          <StatusBadge tone="success">已登录</StatusBadge>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="pwd-current">当前密码</Label>
          <Input
            id="pwd-current"
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => {
              setCurrent(e.target.value);
              setDone(false);
            }}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pwd-new">新密码</Label>
            <Input
              id="pwd-new"
              type="password"
              autoComplete="new-password"
              placeholder="至少 6 位"
              value={next}
              onChange={(e) => {
                setNext(e.target.value);
                setDone(false);
              }}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pwd-confirm">确认新密码</Label>
            <Input
              id="pwd-confirm"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
        </div>
        {mismatch ? <p className="text-sm text-destructive">两次输入的新密码不一致</p> : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {done ? <p className="text-sm text-[var(--success)]">密码已更新</p> : null}
      </CardContent>

      <CardFooter className="justify-end">
        <Button disabled={!valid || changePassword.isPending} onClick={() => void submit()}>
          {changePassword.isPending ? (
            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
          ) : (
            <KeyRound className="mr-1.5 h-4 w-4" />
          )}
          修改密码
        </Button>
      </CardFooter>
    </Card>
  );
}

function LLMSettingsCard() {
  const config = useLLMConfig();
  const save = useSaveLLMConfig();
  const test = useTestLLMConfig();

  const [provider, setProvider] = useState("openai");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [result, setResult] = useState<LLMTestResult | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!config.data) return;
    setProvider(config.data.provider);
    setBaseUrl(config.data.base_url);
    setModel(config.data.model);
  }, [config.data]);

  const buildBody = (): LLMConfigIn => ({
    provider,
    base_url: baseUrl || undefined,
    api_key: apiKey || null,
    model: model || undefined,
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>LLM 大模型</CardTitle>
            <CardDescription>
              推荐与歌单生成使用的模型。OpenAI 兼容接口可覆盖 DeepSeek / OpenRouter / 硅基流动等
            </CardDescription>
          </div>
          <StatusBadge tone={config.data?.source === "runtime" ? "success" : "muted"}>
            {config.data?.source === "runtime" ? "网页配置" : "来自 .env"}
          </StatusBadge>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="provider">Provider</Label>
            <select
              id="provider"
              value={provider}
              onChange={(e) => {
                setProvider(e.target.value);
                setSaved(false);
              }}
              className="rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="openai">OpenAI 兼容</option>
              <option value="mock">Mock（本地无 key 测试）</option>
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="model">模型名</Label>
            <Input
              id="model"
              placeholder="gpt-4o-mini"
              value={model}
              onChange={(e) => {
                setModel(e.target.value);
                setSaved(false);
              }}
            />
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="baseUrl">Base URL</Label>
          <Input
            id="baseUrl"
            placeholder="https://api.openai.com/v1"
            value={baseUrl}
            onChange={(e) => {
              setBaseUrl(e.target.value);
              setSaved(false);
            }}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="llmKey">API Key</Label>
          <Input
            id="llmKey"
            type="password"
            autoComplete="off"
            placeholder={config.data?.has_api_key ? "留空则沿用已保存的 key" : ""}
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value);
              setSaved(false);
            }}
          />
        </div>

        {result ? (
          <div className="rounded-md border border-border bg-muted px-3 py-3 text-sm">
            {result.ok ? (
              <div className="flex flex-col gap-1">
                <StatusBadge tone="success" className="self-start">
                  连接成功
                </StatusBadge>
                <span className="text-muted-foreground">provider={result.provider} · {result.model}</span>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                <StatusBadge tone="danger" className="self-start">
                  连接失败
                </StatusBadge>
                <span className="text-muted-foreground">{result.error}</span>
              </div>
            )}
          </div>
        ) : null}

        {saved ? <p className="text-sm text-[var(--success)]">配置已保存</p> : null}
      </CardContent>

      <CardFooter className="justify-end gap-2">
        <Button
          variant="outline"
          disabled={test.isPending || save.isPending}
          onClick={async () => {
            setResult(await test.mutateAsync(buildBody()));
          }}
        >
          {test.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          测试
        </Button>
        <Button
          disabled={test.isPending || save.isPending}
          onClick={async () => {
            await save.mutateAsync(buildBody());
            setSaved(true);
          }}
        >
          保存
        </Button>
      </CardFooter>
    </Card>
  );
}
