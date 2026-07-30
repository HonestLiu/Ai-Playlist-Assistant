import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

import { AuthGate } from "@/components/auth/AuthGate";
import { AppLayout } from "@/components/layout/AppLayout";
import { AlbumDetailPage } from "@/pages/AlbumDetailPage";
import { AlbumsPage } from "@/pages/AlbumsPage";
import { ArtistDetailPage } from "@/pages/ArtistDetailPage";
import { ArtistsPage } from "@/pages/ArtistsPage";
import { AssistantPage } from "@/pages/AssistantPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { LibraryPage } from "@/pages/LibraryPage";
import { PlaylistDetailPage } from "@/pages/PlaylistDetailPage";
import { LoginPage } from "@/pages/LoginPage";
import { PlaylistsPage } from "@/pages/PlaylistsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { SetupPage } from "@/pages/SetupPage";
import { SongsPage } from "@/pages/SongsPage";
import { HttpError } from "@/services/http";
import { applyTheme, useThemeStore } from "@/stores/theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 10_000,
      // 未登录时重试毫无意义，只会把 401 刷屏
      retry: (failureCount, error) =>
        error instanceof HttpError && error.status === 401 ? false : failureCount < 2,
    },
  },
});

function ThemeEffect() {
  const theme = useThemeStore((state) => state.theme);
  useEffect(() => applyTheme(theme), [theme]);
  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeEffect />
      <Router>
        <Routes>
          {/* 登录与启动引导不套主框架，也不受鉴权网关拦截 */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/setup" element={<SetupPage />} />

          <Route element={<AuthGate />}>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="library" element={<LibraryPage />} />
              <Route path="artists" element={<ArtistsPage />} />
              <Route path="artists/:id" element={<ArtistDetailPage />} />
              <Route path="albums" element={<AlbumsPage />} />
              <Route path="albums/:id" element={<AlbumDetailPage />} />
              <Route path="songs" element={<SongsPage />} />
              <Route path="assistant" element={<AssistantPage />} />
              <Route path="playlists" element={<PlaylistsPage />} />
              <Route path="playlists/:id" element={<PlaylistDetailPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}
