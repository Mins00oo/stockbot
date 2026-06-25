/**
 * expo-secure-store wrapper for the app pairing key.
 *
 * Only the PAIRING KEY is stored on-device (encrypted via SecureStore).
 * The Toss API keys are NOT stored here — they are encrypted and persisted
 * by the backend (see API_정의서 / tech-stack: "토스 키는 백엔드에 암호화 저장").
 */
import * as SecureStore from "expo-secure-store";

const PAIRING_KEY = "stockbot.pairingKey";

export async function setPairingKey(key: string): Promise<void> {
  await SecureStore.setItemAsync(PAIRING_KEY, key, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED,
  });
}

export async function getPairingKey(): Promise<string | null> {
  return SecureStore.getItemAsync(PAIRING_KEY);
}

export async function clearPairingKey(): Promise<void> {
  await SecureStore.deleteItemAsync(PAIRING_KEY);
}

/** Clear all locally-stored secrets (used by "계좌 다시 연동"). */
export async function clear(): Promise<void> {
  await clearPairingKey();
}
