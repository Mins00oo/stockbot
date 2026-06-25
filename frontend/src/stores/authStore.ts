/**
 * Zustand auth/session store (minimal — per state-management principle:
 * Zustand only for cross-screen, non-server session flags).
 *
 *  - paired:    pairing key verified + stored in SecureStore
 *  - connected: Toss account connected (backend has the encrypted keys)
 *  - hydrated:  we've finished reading SecureStore on launch (auth-gate ready)
 */
import { create } from "zustand";

import { clear as clearSecure, getPairingKey } from "@/lib/secureStore";

interface AuthState {
  paired: boolean;
  connected: boolean;
  hydrated: boolean;

  setPaired: (v: boolean) => void;
  setConnected: (v: boolean) => void;
  /** Read SecureStore once at app launch to decide the initial route. */
  hydrate: () => Promise<void>;
  /** Wipe local secrets + reset flags (계좌 다시 연동 / logout). */
  reset: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  paired: false,
  connected: false,
  hydrated: false,

  setPaired: (v) => set({ paired: v }),
  setConnected: (v) => set({ connected: v }),

  hydrate: async () => {
    const key = await getPairingKey();
    set({ paired: !!key, hydrated: true });
  },

  reset: async () => {
    await clearSecure();
    set({ paired: false, connected: false });
  },
}));
