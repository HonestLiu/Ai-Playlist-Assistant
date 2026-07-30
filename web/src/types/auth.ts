export interface User {
  id: number;
  username: string;
  is_admin: boolean;
  created_at: string;
}

export interface SessionState {
  auth_enabled: boolean;
  needs_bootstrap: boolean;
  authenticated: boolean;
  user: User | null;
  onboarding_completed: boolean;
}

export interface LoginIn {
  username: string;
  password: string;
  remember?: boolean;
}

export interface BootstrapIn {
  username: string;
  password: string;
}

export interface ChangePasswordIn {
  current_password: string;
  new_password: string;
}

export interface SetupStatus {
  needs_bootstrap: boolean;
  account_ready: boolean;
  subsonic_configured: boolean;
  subsonic_connected: boolean | null;
  llm_configured: boolean;
  llm_provider: string;
  library_synced: boolean;
  song_count: number;
  completed: boolean;
}
