import { useMutation } from "@tanstack/react-query";

import { connectToss } from "@/api/auth";
import { useAuthStore } from "@/stores/authStore";
import type { TossConnectRequest } from "@/types/api";

/**
 * Connect the Toss account (backend stores the encrypted keys).
 * On success, flip the `connected` flag.
 */
export function useConnectToss() {
  const setConnected = useAuthStore((s) => s.setConnected);

  return useMutation({
    mutationFn: (body: TossConnectRequest) => connectToss(body),
    onSuccess: (res) => setConnected(res.connected),
  });
}
