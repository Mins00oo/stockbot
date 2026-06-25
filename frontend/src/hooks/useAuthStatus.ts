import { useQuery } from "@tanstack/react-query";

import { getAuthStatus } from "@/api/auth";
import type { AuthStatusResponse } from "@/types/api";

export const authStatusQueryKey = ["auth", "status"] as const;

/**
 * Launch-gate connection check. Asks the backend whether the Toss account is
 * connected (source of truth). Only runs once paired (a pairing key exists).
 */
export function useAuthStatus(enabled: boolean) {
  return useQuery<AuthStatusResponse>({
    queryKey: authStatusQueryKey,
    queryFn: getAuthStatus,
    enabled,
    staleTime: 0,
    retry: 1,
  });
}
