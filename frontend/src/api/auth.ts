import { api, withPairingKeyHeader } from "./client";

import {
  AuthStatusResponseSchema,
  PairingVerifyResponseSchema,
  TossConnectRequestSchema,
  TossConnectResponseSchema,
  type AuthStatusResponse,
  type PairingVerifyResponse,
  type TossConnectRequest,
  type TossConnectResponse,
} from "@/types/api";

/**
 * ② POST /auth/pairing/verify
 * The key is sent via the X-Pairing-Key header (not the body).
 * During onboarding we pass the candidate key explicitly so verification
 * happens BEFORE we persist it to SecureStore.
 */
export async function verifyPairing(
  pairingKey: string,
): Promise<PairingVerifyResponse> {
  const res = await api.post(
    "/auth/pairing/verify",
    undefined,
    withPairingKeyHeader(pairingKey),
  );
  return PairingVerifyResponseSchema.parse(res.data);
}

/**
 * ③ POST /auth/toss/connect
 * Pairing key comes from the request interceptor (already stored after step 1).
 */
export async function connectToss(
  body: TossConnectRequest,
): Promise<TossConnectResponse> {
  const payload = TossConnectRequestSchema.parse(body);
  const res = await api.post("/auth/toss/connect", payload);
  return TossConnectResponseSchema.parse(res.data);
}

/**
 * GET /auth/status — launch-gate connection check.
 * `connected` is the backend's truth (it holds the encrypted Toss keys).
 * Pairing key is attached by the request interceptor.
 */
export async function getAuthStatus(): Promise<AuthStatusResponse> {
  const res = await api.get("/auth/status");
  return AuthStatusResponseSchema.parse(res.data);
}
