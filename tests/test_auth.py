from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

import requests

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.auth import (
    AuthError,
    SupabaseAuthClient,
    SupabaseAuthConfig,
    normalize_email,
    personal_workspace_code,
    resolve_auth_config,
)


USER_ID = "f4a0613e-42af-4e7f-973d-532f52393be1"


def response(status: int, payload: dict | None = None) -> Mock:
    result = Mock(spec=requests.Response)
    result.status_code = status
    result.ok = 200 <= status < 300
    result.content = b"" if payload is None else b"json"
    result.json.return_value = payload or {}
    return result


class SupabaseAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.http = Mock(spec=requests.Session)
        self.client = SupabaseAuthClient(
            SupabaseAuthConfig("https://project.supabase.co", "sb_publishable_test"),
            session=self.http,
            timeout=3,
        )

    def test_resolve_config_accepts_publishable_and_legacy_anon_keys(self) -> None:
        modern = resolve_auth_config(
            {"SUPABASE_URL": "https://project.supabase.co", "SUPABASE_PUBLISHABLE_KEY": "new"},
            {},
        )
        legacy = resolve_auth_config(
            {"SUPABASE_URL": "https://project.supabase.co", "SUPABASE_ANON_KEY": "legacy"},
            {},
        )
        self.assertEqual(modern.publishable_key, "new")
        self.assertEqual(legacy.publishable_key, "legacy")
        self.assertIsNone(resolve_auth_config({}, {}))

    def test_config_rejects_non_https_url(self) -> None:
        with self.assertRaises(ValueError):
            SupabaseAuthConfig("http://project.supabase.co", "key")

    def test_send_otp_normalizes_email_and_uses_publishable_key(self) -> None:
        self.http.request.return_value = response(200)
        email = self.client.send_email_otp(" USER@Example.COM ")
        self.assertEqual(email, "user@example.com")
        kwargs = self.http.request.call_args.kwargs
        self.assertEqual(kwargs["json"], {"email": email, "create_user": True})
        self.assertEqual(kwargs["headers"]["apikey"], "sb_publishable_test")
        self.assertNotIn("Authorization", kwargs["headers"])

    def test_verify_otp_returns_safe_session(self) -> None:
        self.http.request.return_value = response(
            200,
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
                "user": {"id": USER_ID, "email": "user@example.com"},
            },
        )
        session = self.client.verify_email_otp("user@example.com", "123456")
        self.assertEqual(session.user["id"], USER_ID)
        self.assertEqual(session.as_dict()["refresh_token"], "refresh")
        self.assertGreater(session.expires_at, 0)

    def test_verify_otp_rejects_invalid_shape_before_network(self) -> None:
        with self.assertRaises(AuthError):
            self.client.verify_email_otp("user@example.com", "12ab")
        self.http.request.assert_not_called()

    def test_refresh_and_local_logout_use_bearer_token(self) -> None:
        self.http.request.side_effect = [
            response(
                200,
                {
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 3600,
                    "user": {"id": USER_ID},
                },
            ),
            response(204),
        ]
        refreshed = self.client.refresh_session("old-refresh")
        self.client.sign_out(refreshed.access_token)
        self.assertEqual(refreshed.refresh_token, "new-refresh")
        logout_call = self.http.request.call_args
        self.assertIn("scope=local", logout_call.args[1])
        self.assertEqual(logout_call.kwargs["headers"]["Authorization"], "Bearer new-access")

    def test_rate_limit_and_network_errors_are_safe(self) -> None:
        self.http.request.return_value = response(429, {"message": "internal detail"})
        with self.assertRaisesRegex(AuthError, "انتظر دقيقة"):
            self.client.send_email_otp("user@example.com")
        self.http.request.side_effect = requests.ConnectionError("secret host detail")
        with self.assertRaisesRegex(AuthError, "تعذر الاتصال"):
            self.client.send_email_otp("user@example.com")

    def test_auth_error_codes_explain_configuration_problem(self) -> None:
        cases = (
            (403, "email_address_not_authorized", "Custom SMTP"),
            (400, "email_provider_disabled", "Providers"),
            (400, "otp_disabled", "OTP"),
            (429, "over_email_send_rate_limit", "حد إرسال"),
            (500, "unexpected_failure", "Auth Logs"),
        )
        for status, code, expected in cases:
            with self.subTest(code=code):
                self.http.request.side_effect = None
                self.http.request.return_value = response(status, {"error_code": code})
                with self.assertRaisesRegex(AuthError, expected):
                    self.client.send_email_otp("user@example.com")

    def test_invalid_project_credentials_have_safe_message(self) -> None:
        self.http.request.return_value = response(401, {"message": "Invalid API key"})
        with self.assertRaisesRegex(AuthError, "SUPABASE_URL"):
            self.client.send_email_otp("user@example.com")

    def test_identity_helpers_validate_input(self) -> None:
        self.assertEqual(normalize_email("A@Example.com"), "a@example.com")
        self.assertEqual(personal_workspace_code(USER_ID), f"qareena-user:{USER_ID}")
        with self.assertRaises(AuthError):
            normalize_email("not-an-email")
        with self.assertRaises(AuthError):
            personal_workspace_code("not-a-uuid")


if __name__ == "__main__":
    unittest.main()
