import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { authApi, authKeys } from "@/services/auth";
import type { BootstrapIn, ChangePasswordIn, LoginIn } from "@/types/auth";

/** 会话状态。它决定渲染登录页 / 引导页 / 主界面，因此不缓存过久。 */
export function useSession() {
  return useQuery({
    queryKey: authKeys.session,
    queryFn: authApi.session,
    staleTime: 0,
    retry: false,
  });
}

export function useSetupStatus(probe = false, enabled = true) {
  return useQuery({
    queryKey: authKeys.setupStatus(probe),
    queryFn: () => authApi.setupStatus(probe),
    enabled,
    retry: false,
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: LoginIn) => authApi.login(body),
    onSuccess: (data) => {
      qc.setQueryData(authKeys.session, data);
      // 登录前所有请求都是 401，缓存里全是错误态，整体重来一遍
      void qc.invalidateQueries();
    },
  });
}

export function useBootstrap() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: BootstrapIn) => authApi.bootstrap(body),
    onSuccess: (data) => {
      qc.setQueryData(authKeys.session, data);
      void qc.invalidateQueries();
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      qc.clear();
      void qc.invalidateQueries({ queryKey: authKeys.session });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (body: ChangePasswordIn) => authApi.changePassword(body),
  });
}

export function useCompleteSetup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => authApi.completeSetup(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: authKeys.session });
    },
  });
}
