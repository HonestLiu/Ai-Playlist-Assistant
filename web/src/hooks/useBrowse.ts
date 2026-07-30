import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type { ListQuery } from "@/types/library";

interface Page<T> {
  items: T[];
  total: number;
}

/**
 * 通用浏览 hook：处理「搜索防抖 + 分页加载更多」。
 * 三张列表页（艺术家 / 专辑 / 歌曲）共用，避免重复逻辑。
 *
 * - ``queryKeyBase``：用于区分不同资源的缓存。
 * - ``fetcher``：传入当前页参数，返回 ``{ items, total }``。
 * - ``fixedParams``：固定过滤条件（如某艺术家的专辑）。
 */
export function useBrowse<T extends { id: string }>(
  queryKeyBase: string,
  fetcher: (params: ListQuery) => Promise<Page<T>>,
  fixedParams: ListQuery = {},
  pageSize = 60,
) {
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState<T[]>([]);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  const fixedKey = JSON.stringify(fixedParams);
  useEffect(() => {
    setOffset(0);
    setItems([]);
  }, [debouncedQ, fixedKey]);

  const params: ListQuery = {
    ...fixedParams,
    q: debouncedQ || undefined,
    limit: pageSize,
    offset,
  };

  const { data, isFetching, isLoading } = useQuery({
    queryKey: [queryKeyBase, fixedKey, debouncedQ, offset],
    queryFn: () => fetcher(params),
  });

  useEffect(() => {
    if (!data) return;
    setItems((prev) => (offset === 0 ? [...data.items] : [...prev, ...data.items]));
  }, [data, offset]);

  return {
    q,
    setQ,
    items,
    total: data?.total ?? 0,
    hasMore: offset + pageSize < (data?.total ?? 0),
    loadMore: () => setOffset((o) => o + pageSize),
    isFetching,
    isLoading,
  };
}
