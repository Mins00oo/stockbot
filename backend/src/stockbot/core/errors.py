"""Central error catalog.

Single source of truth for code / HTTP status / user-facing message.
Services raise these typed exceptions and never format error bodies inline;
the global handlers (error_handlers.py) turn them into the standard envelope.

Messages mirror the API 정의서 error catalog exactly.
"""

from __future__ import annotations


class AppError(Exception):
    """Base application error.

    Subclasses set ``code``, ``status`` and a default ``message``.
    """

    code: str = "INTERNAL"
    status: int = 500
    message: str = "일시적인 오류가 발생했어요"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class Unauthorized(AppError):
    code = "UNAUTHORIZED"
    status = 401
    message = "페어링 키가 올바르지 않아요"


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status = 422
    message = "입력값이 올바르지 않아요"


class TossAuthFailed(AppError):
    code = "TOSS_AUTH_FAILED"
    status = 400
    message = "토스 키가 올바르지 않아요"


class NotConnected(AppError):
    code = "NOT_CONNECTED"
    status = 409
    message = "토스 계좌를 먼저 연결해 주세요"


class TossUnavailable(AppError):
    code = "TOSS_UNAVAILABLE"
    status = 502
    message = "토스 서버에 연결할 수 없어요"


class Internal(AppError):
    code = "INTERNAL"
    status = 500
    message = "일시적인 오류가 발생했어요"
