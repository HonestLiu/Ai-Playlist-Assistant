import { request } from "@/services/http";
import type {
  BootstrapIn,
  ChangePasswordIn,
  LoginIn,
  SessionState,
  SetupStatus,
  User,
} from "@/types/auth";

export const authKeys = {
  session: ["auth", "session"] as const,
  setupStatus: (probe: boolean) => ["auth", "setup-status", probe] as const,
};

export const authApi = {
  session: () => request<SessionState>("/auth/session"),
  login: (body: LoginIn) =>
    request<SessionState>("/auth/login", { method: "POST", body }),
  bootstrap: (body: BootstrapIn) =>
    request<SessionState>("/auth/bootstrap", { method: "POST", body }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  changePassword: (body: ChangePasswordIn) =>
    request<User>("/auth/password", { method: "POST", body }),

  setupStatus: (probe = false) =>
    request<SetupStatus>(`/setup/status${probe ? "?probe=true" : ""}`),
  completeSetup: () => request<SetupStatus>("/setup/complete", { method: "POST" }),
};
