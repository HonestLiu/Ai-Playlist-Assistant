/** 与服务端 schema 一一对应的类型定义。 */

export interface ApiError {
  code: string;
  message: string;
  detail?: unknown;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  debug: boolean;
}

export interface SubsonicServerInfo {
  version: string | null;
  server_type: string | null;
  server_version: string | null;
  open_subsonic: boolean;
}

export interface ConnectionStatus {
  configured: boolean;
  connected: boolean;
  url: string | null;
  username: string | null;
  server: SubsonicServerInfo | null;
  latency_ms: number | null;
  error_code: string | null;
  error_message: string | null;
  checked_at: string;
}

export interface SubsonicConfigOut {
  url: string;
  username: string;
  has_password: boolean;
  legacy_auth: boolean;
  verify_ssl: boolean;
  source: "env" | "runtime";
  configured: boolean;
}

export interface SubsonicConfigIn {
  url: string;
  username: string;
  password?: string | null;
  legacy_auth: boolean;
  verify_ssl: boolean;
}
