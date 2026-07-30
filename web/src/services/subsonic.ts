/** Subsonic / 设置相关的接口调用。 */
import { request } from "@/services/http";
import type {
  ConnectionStatus,
  HealthResponse,
  SubsonicConfigIn,
  SubsonicConfigOut,
} from "@/types/api";

export const subsonicApi = {
  health: () => request<HealthResponse>("/health"),
  status: () => request<ConnectionStatus>("/subsonic/status"),
  getConfig: () => request<SubsonicConfigOut>("/settings/subsonic"),
  saveConfig: (body: SubsonicConfigIn) =>
    request<SubsonicConfigOut>("/settings/subsonic", { method: "PUT", body }),
  testConfig: (body: SubsonicConfigIn) =>
    request<ConnectionStatus>("/settings/subsonic/test", { method: "POST", body }),
  resetConfig: () => request<void>("/settings/subsonic", { method: "DELETE" }),
};

export const queryKeys = {
  health: ["health"] as const,
  subsonicStatus: ["subsonic", "status"] as const,
  subsonicConfig: ["settings", "subsonic"] as const,
};
