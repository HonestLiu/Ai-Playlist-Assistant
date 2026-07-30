import {
  Album,
  Disc3,
  LayoutDashboard,
  ListMusic,
  LogOut,
  Moon,
  Music,
  Music2,
  Settings,
  Sparkles,
  Sun,
  UserRound,
  Wrench,
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { PlayerBar } from "@/components/player/PlayerBar";
import { useLogout, useSession } from "@/hooks/useAuth";
import { useSubsonicStatus } from "@/hooks/useSubsonic";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/stores/theme";

const navItems = [
  { to: "/", label: "总览", icon: LayoutDashboard, end: true },
  { to: "/library", label: "音乐库", icon: Disc3, end: false },
  { to: "/artists", label: "艺术家", icon: Music2, end: false },
  { to: "/albums", label: "专辑", icon: Album, end: false },
  { to: "/songs", label: "歌曲", icon: Music, end: false },
  { to: "/tools", label: "工具箱", icon: Wrench, end: false },
  { to: "/assistant", label: "AI 助手", icon: Sparkles, end: false },
  { to: "/playlists", label: "歌单", icon: ListMusic, end: false },
  { to: "/settings", label: "设置", icon: Settings, end: false },
];

function ConnectionIndicator() {
  const { data, isLoading, isError } = useSubsonicStatus();

  if (isLoading) return <StatusBadge tone="muted">检测中</StatusBadge>;
  if (isError) return <StatusBadge tone="danger">服务端离线</StatusBadge>;
  if (!data?.configured) return <StatusBadge tone="warning">未配置</StatusBadge>;
  if (!data.connected) return <StatusBadge tone="danger">连接失败</StatusBadge>;
  return <StatusBadge tone="success">已连接</StatusBadge>;
}

function UserMenu() {
  const session = useSession();
  const logout = useLogout();
  const navigate = useNavigate();

  const user = session.data?.user;
  if (!session.data?.auth_enabled) return null;

  return (
    <div className="flex items-center gap-1.5">
      {user ? (
        <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <UserRound className="h-4 w-4" />
          {user.username}
        </span>
      ) : null}
      <Button
        variant="ghost"
        size="icon"
        aria-label="登出"
        title="登出"
        disabled={logout.isPending}
        onClick={async () => {
          await logout.mutateAsync();
          navigate("/login", { replace: true });
        }}
      >
        <LogOut className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function AppLayout() {
  const { theme, toggle } = useThemeStore();

  return (
    <div className="flex h-full">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-sidebar md:flex">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Disc3 className="h-4.5 w-4.5" />
          </span>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-medium">歌单助手</span>
            <span className="text-xs text-muted-foreground">Subsonic + AI</span>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-accent font-medium text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 text-xs text-muted-foreground">AI 音乐歌单助手</div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-border px-6">
          <ConnectionIndicator />
          <div className="flex items-center gap-1">
            <UserMenu />
            <Button variant="ghost" size="icon" onClick={toggle} aria-label="切换主题">
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </header>

        <main className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
          <Outlet />
        </main>
        <PlayerBar />
      </div>
    </div>
  );
}
