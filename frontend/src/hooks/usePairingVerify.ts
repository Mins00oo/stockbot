import { useMutation } from "@tanstack/react-query";

import { verifyPairing } from "@/api/auth";
import { setPairingKey } from "@/lib/secureStore";
import { useAuthStore } from "@/stores/authStore";

/**
 * Verify pairing key, then (on success) persist it to SecureStore and flip
 * the `paired` flag. The key is the mutation variable.
 */
export function usePairingVerify() {
  const setPaired = useAuthStore((s) => s.setPaired);

  return useMutation({
    mutationFn: async (pairingKey: string) => {
      const res = await verifyPairing(pairingKey);
      if (!res.valid) {
        throw new Error("INVALID_PAIRING");
      }
      await setPairingKey(pairingKey);
      return res;
    },
    onSuccess: () => setPaired(true),
  });
}
