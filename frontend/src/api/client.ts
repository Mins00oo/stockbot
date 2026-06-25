/**
 * Axios instance.
 * - baseURL from EXPO_PUBLIC_API_URL
 * - request interceptor auto-attaches X-Pairing-Key from SecureStore
 * - response interceptor normalizes { error: { code, message } } into a typed ApiError
 */
import axios, { AxiosError, type AxiosInstance } from "axios";

import { getPairingKey } from "@/lib/secureStore";
import { ApiErrorBodySchema, type ApiErrorCode } from "@/types/api";

const baseURL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/** Typed error thrown by every failed request. */
export class ApiError extends Error {
  code: ApiErrorCode;
  status?: number;

  constructor(code: ApiErrorCode, message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// Attach pairing key on every request (except where explicitly skipped).
api.interceptors.request.use(async (config) => {
  const key = await getPairingKey();
  if (key) {
    config.headers.set("X-Pairing-Key", key);
  }
  return config;
});

// Normalize errors to ApiError.
api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    // Network / no response.
    if (!error.response) {
      return Promise.reject(
        new ApiError("NETWORK", "네트워크 연결을 확인해 주세요"),
      );
    }

    const status = error.response.status;
    const parsed = ApiErrorBodySchema.safeParse(error.response.data);
    if (parsed.success) {
      return Promise.reject(
        new ApiError(
          parsed.data.error.code as ApiErrorCode,
          parsed.data.error.message,
          status,
        ),
      );
    }

    // Fallback when body isn't in the standard shape.
    return Promise.reject(
      new ApiError("UNKNOWN", "일시적인 오류가 발생했어요", status),
    );
  },
);

/**
 * Verify the pairing key by sending it as a header WITHOUT relying on the
 * stored value (used during onboarding before we persist it).
 */
export function withPairingKeyHeader(key: string) {
  return { headers: { "X-Pairing-Key": key } };
}
