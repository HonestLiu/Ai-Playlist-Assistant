/**
 * 唯一的 HTTP 出口。
 * 组件与 hook 不允许直接调用 fetch，统一走这里，方便加超时、鉴权、埋点。
 */
import type { ApiError } from "@/types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export class HttpError extends Error {
  readonly code: string;
  readonly status: number;
  readonly detail?: unknown;

  constructor(status: number, payload: ApiError) {
    super(payload.message);
    this.name = "HttpError";
    this.status = status;
    this.code = payload.code;
    this.detail = payload.detail;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  body?: unknown;
  signal?: AbortSignal;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = options;

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      signal,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    throw new HttpError(0, {
      code: "network_error",
      message: "无法连接到本地服务端，确认 uvicorn 是否已启动",
      detail: String(error),
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const payload = text ? (JSON.parse(text) as unknown) : null;

  if (!response.ok) {
    const apiError: ApiError =
      payload && typeof payload === "object" && "code" in payload
        ? (payload as ApiError)
        : { code: "unknown_error", message: `请求失败（HTTP ${response.status}）` };
    throw new HttpError(response.status, apiError);
  }

  return payload as T;
}
