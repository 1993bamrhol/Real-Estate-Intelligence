from __future__ import annotations

from dataclasses import dataclass
import os
import re
import time
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import UUID

import requests


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
AUTH_TIMEOUT_SECONDS = 15


class AuthError(RuntimeError):
    """A safe, user-facing Supabase Auth error."""


@dataclass(frozen=True)
class SupabaseAuthConfig:
    url: str
    publishable_key: str

    def __post_init__(self) -> None:
        normalized_url = str(self.url or "").strip().rstrip("/")
        parsed = urlparse(normalized_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("SUPABASE_URL must be a valid HTTPS URL.")
        normalized_key = str(self.publishable_key or "").strip()
        if not normalized_key:
            raise ValueError("A Supabase publishable or anon key is required.")
        object.__setattr__(self, "url", normalized_url)
        object.__setattr__(self, "publishable_key", normalized_key)


@dataclass(frozen=True)
class AuthSession:
    access_token: str
    refresh_token: str
    expires_at: int
    user: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "AuthSession":
        access_token = str(payload.get("access_token") or "")
        refresh_token = str(payload.get("refresh_token") or "")
        user = payload.get("user")
        if not access_token or not refresh_token or not isinstance(user, dict) or not user.get("id"):
            raise AuthError("لم تُنشأ جلسة دخول صالحة. أعد طلب الرمز ثم حاول مرة أخرى.")
        expires_in = max(_integer(payload.get("expires_in"), 3600), 60)
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=int(time.time()) + expires_in,
            user=dict(user),
        )

    @classmethod
    def restore(cls, payload: Mapping[str, Any]) -> "AuthSession":
        user = payload.get("user")
        if not isinstance(user, dict):
            raise AuthError("جلسة المستخدم غير صالحة.")
        return cls(
            access_token=str(payload.get("access_token") or ""),
            refresh_token=str(payload.get("refresh_token") or ""),
            expires_at=_integer(payload.get("expires_at"), 0),
            user=dict(user),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "user": dict(self.user),
        }


class SupabaseAuthClient:
    def __init__(
        self,
        config: SupabaseAuthConfig,
        *,
        session: requests.Session | None = None,
        timeout: int = AUTH_TIMEOUT_SECONDS,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.timeout = timeout

    def send_email_otp(self, email: str, *, create_user: bool = True) -> str:
        normalized_email = normalize_email(email)
        self._request(
            "POST",
            "/auth/v1/otp",
            json={"email": normalized_email, "create_user": bool(create_user)},
            fallback="تعذر إرسال رمز الدخول. تحقق من البريد وحاول مرة أخرى.",
        )
        return normalized_email

    def verify_email_otp(self, email: str, token: str) -> AuthSession:
        normalized_email = normalize_email(email)
        normalized_token = str(token or "").strip().replace(" ", "")
        if not re.fullmatch(r"\d{6}", normalized_token):
            raise AuthError("رمز التحقق يجب أن يتكون من 6 أرقام.")
        payload = self._request(
            "POST",
            "/auth/v1/verify",
            json={"email": normalized_email, "token": normalized_token, "type": "email"},
            fallback="رمز التحقق غير صحيح أو انتهت صلاحيته.",
        )
        return AuthSession.from_payload(payload)

    def refresh_session(self, refresh_token: str) -> AuthSession:
        token = str(refresh_token or "").strip()
        if not token:
            raise AuthError("انتهت جلسة الدخول. سجل الدخول مرة أخرى.")
        payload = self._request(
            "POST",
            "/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": token},
            fallback="انتهت جلسة الدخول. سجل الدخول مرة أخرى.",
        )
        return AuthSession.from_payload(payload)

    def get_user(self, access_token: str) -> dict[str, Any]:
        payload = self._request(
            "GET",
            "/auth/v1/user",
            access_token=access_token,
            fallback="تعذر التحقق من هوية المستخدم.",
        )
        if not payload.get("id"):
            raise AuthError("تعذر التحقق من هوية المستخدم.")
        return payload

    def sign_out(self, access_token: str) -> None:
        self._request(
            "POST",
            "/auth/v1/logout?scope=local",
            access_token=access_token,
            fallback="تعذر إنهاء الجلسة على الخادم.",
            allow_empty=True,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        access_token: str | None = None,
        fallback: str,
        allow_empty: bool = False,
    ) -> dict[str, Any]:
        headers = {
            "apikey": self.config.publishable_key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        try:
            response = self.session.request(
                method,
                f"{self.config.url}{path}",
                headers=headers,
                json=json,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise AuthError("تعذر الاتصال بخدمة تسجيل الدخول. حاول مرة أخرى.") from exc
        if not response.ok:
            raise AuthError(_safe_error(response, fallback))
        if response.status_code == 204 or not response.content:
            return {} if allow_empty else {}
        try:
            payload = response.json()
        except ValueError as exc:
            raise AuthError(fallback) from exc
        if not isinstance(payload, dict):
            raise AuthError(fallback)
        return payload


def resolve_auth_config(
    secrets: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> SupabaseAuthConfig | None:
    secret_values = secrets if secrets is not None else {}
    environment = environ if environ is not None else os.environ
    url = str(secret_values.get("SUPABASE_URL") or environment.get("SUPABASE_URL") or "").strip()
    key = str(
        secret_values.get("SUPABASE_PUBLISHABLE_KEY")
        or secret_values.get("SUPABASE_ANON_KEY")
        or environment.get("SUPABASE_PUBLISHABLE_KEY")
        or environment.get("SUPABASE_ANON_KEY")
        or ""
    ).strip()
    if not url and not key:
        return None
    return SupabaseAuthConfig(url=url, publishable_key=key)


def normalize_email(email: str) -> str:
    normalized = str(email or "").strip().lower()
    if len(normalized) > 254 or not EMAIL_PATTERN.fullmatch(normalized):
        raise AuthError("اكتب بريدًا إلكترونيًا صحيحًا.")
    return normalized


def personal_workspace_code(user_id: str) -> str:
    try:
        normalized = str(UUID(str(user_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise AuthError("معرّف المستخدم غير صالح.") from exc
    return f"qareena-user:{normalized}"


def _safe_error(response: requests.Response, fallback: str) -> str:
    if response.status_code == 429:
        return "تم طلب رموز كثيرة. انتظر دقيقة ثم أعد المحاولة."
    try:
        payload = response.json()
    except ValueError:
        return fallback
    raw = " ".join(
        str(payload.get(key) or "")
        for key in ("code", "error", "error_code", "msg", "message", "error_description")
    ).lower()
    if any(word in raw for word in ("expired", "invalid token", "otp_expired", "token has expired")):
        return "رمز التحقق غير صحيح أو انتهت صلاحيته."
    if "email" in raw and any(word in raw for word in ("invalid", "not allowed", "unable to validate")):
        return "تعذر استخدام هذا البريد. تحقق منه أو راجع إعدادات البريد في Supabase."
    return fallback


def _integer(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
