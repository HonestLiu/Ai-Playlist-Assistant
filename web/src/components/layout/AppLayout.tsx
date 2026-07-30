import {
  Album,
  Disc3,
  LayoutDashboard,
  ListMusic,
  Moon,
  Music,
  Music2,
  Settings,
  Sparkles,
  Sun,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { useSubsonicStatus } from "@/hooks/useSubsonic";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/stores/theme";

const navItems = [
  { to: "/", label: "总览", icon: LayoutDashboard, end: true },
  { to: "/library", label: "音乐库", icon: Disc3, end: false },
  { to: "/artists", label: "艺术家", icon: Music2, end: false },
  { to: "/albums", label: "专辑", icon: Album, end: false },
  { to: "/songs", label: "歌曲", icon: Music, end: false },
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

        <div className="px-5 py-4 text-xs text-muted-foreground">Phase 4 · 每日推荐</div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-border px-6">
          <ConnectionIndicator />
          <Button variant="ghost" size="icon" onClick={toggle} aria-label="切换主题">
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </header>

        <main className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
