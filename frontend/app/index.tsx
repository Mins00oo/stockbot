import { Redirect } from "expo-router";

import { useAuthStore } from "@/stores/authStore";

/**
 * Auth-gate entry. After hydration:
 *  - paired (pairing key in SecureStore) -> tabs (home)
 *  - not paired                          -> onboarding intro
 *
 * NOTE: "paired" only means the pairing key exists locally. Whether Toss is
 * connected is enforced by the backend (NOT_CONNECTED 409 on /portfolio/holdings),
 * which the home screen surfaces with a "다시 연동" path.
 */
export default function Index() {
  const paired = useAuthStore((s) => s.paired);

  if (paired) {
    return <Redirect href="/(tabs)/home" />;
  }
  return <Redirect href="/onboarding/intro" />;
}
