from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "byteplus-cloud" / "scripts" / "byteplus_doctor.py"
SPEC = importlib.util.spec_from_file_location("byteplus_doctor", MODULE_PATH)
assert SPEC and SPEC.loader
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


class DoctorTests(unittest.TestCase):
    def test_redacts_sensitive_keys_and_text(self) -> None:
        value = {
            "AccessKeyId": "AK-should-not-appear",
            "nested": {"session_token": "token-should-not-appear"},
            "X-Tos-Signature": "dict-signature",
            "Cookie": "dict-cookie",
            "message": "authorization=Bearer-secret",
            "json_message": '{"AccessKeyId":"json-secret"}',
            "signed_url": (
                "https://bucket.example/object?X-"
                "Tos-Credential=url-credential&X-"
                "Tos-Signature=url-signature"
            ),
            "AccountId": "safe-account-id",
        }
        redacted = doctor.redact_value(value)
        serialized = json.dumps(redacted)
        self.assertNotIn("AK-should-not-appear", serialized)
        self.assertNotIn("token-should-not-appear", serialized)
        self.assertNotIn("dict-signature", serialized)
        self.assertNotIn("dict-cookie", serialized)
        self.assertNotIn("Bearer-secret", serialized)
        self.assertNotIn("json-secret", serialized)
        self.assertNotIn("url-credential", serialized)
        self.assertNotIn("url-signature", serialized)
        self.assertIn("safe-account-id", serialized)

    def test_redacts_secrets_from_unstructured_command_output(self) -> None:
        raw = (
            'failed with {"AccessKeyId":"json-secret"} '
            "password=plain-secret "
            "Authorization: Bearer bearer-secret.with.parts\n"
            "-----BEGIN OPENSSH "
            "PRIVATE KEY-----\n"
            "private-key-body\n"
            "-----END OPENSSH "
            "PRIVATE KEY-----\n"
            "https://example.test/?X-"
            "Amz-Signature=query-secret&X-"
            "Tos-Security-Token=security-token-secret"
        )
        sanitized = doctor.redact_text(raw)
        self.assertNotIn("json-secret", sanitized)
        self.assertNotIn("plain-secret", sanitized)
        self.assertNotIn("bearer-secret.with.parts", sanitized)
        self.assertNotIn("private-key-body", sanitized)
        self.assertNotIn("query-secret", sanitized)
        self.assertNotIn("security-token-secret", sanitized)

    def test_auth_check_requires_an_explicit_profile_and_region(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            doctor.parse_args(["--check-auth", "--profile", "dev"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("requires both --profile and --region", stderr.getvalue())

    def test_profile_inspection_never_returns_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "current": "dev",
                        "profiles": {
                            "dev": {
                                "mode": "console-login",
                                "region": "ap-southeast-1",
                                "access-key": "secret-ak",
                                "secret-key": "secret-sk",
                                "session-token": "secret-token",
                                "login-session": {"refresh-token": "secret-refresh"},
                            },
                            "corp": {
                                "mode": "sso",
                                "region": "ap-southeast-1",
                                "sso-session-name": "company",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            path.chmod(0o600)
            result = doctor.inspect_profiles(path)
            serialized = json.dumps(result)
            self.assertNotIn("secret-ak", serialized)
            self.assertNotIn("secret-sk", serialized)
            self.assertNotIn("secret-token", serialized)
            self.assertNotIn("secret-refresh", serialized)
            self.assertEqual(result["profile_count"], 2)
            if os.name == "nt":
                self.assertIsNone(result["permissions"]["owner_only"])
                self.assertFalse(result["permissions"]["supported"])
            else:
                self.assertTrue(result["permissions"]["owner_only"])
                self.assertTrue(result["permissions"]["supported"])
            self.assertEqual(result["profiles"][0]["name"], "<profile-1>")
            self.assertEqual(result["profiles"][1]["name"], "<profile-2>")
            self.assertEqual(result["current"], "<configured>")
            self.assertEqual(result["profiles"][0]["mode"], "sso")
            self.assertEqual(result["profiles"][1]["mode"], "console-login")

            detailed = doctor.inspect_profiles(path, show_identifiers=True)
            self.assertEqual(detailed["profiles"][0]["name"], "corp")
            self.assertEqual(detailed["profiles"][1]["name"], "dev")
            self.assertEqual(detailed["current"], "dev")

    def test_detects_weak_config_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text('{"profiles": {}}', encoding="utf-8")
            path.chmod(0o644)
            result = doctor.inspect_profiles(path)
            if os.name == "nt":
                self.assertIsNone(result["permissions"]["owner_only"])
            else:
                self.assertFalse(result["permissions"]["owner_only"])

    def test_reports_empty_config_as_unconfigured(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text("", encoding="utf-8")
            path.chmod(0o600)
            result = doctor.inspect_profiles(path)
            self.assertEqual(result["state"], "empty")
            self.assertEqual(
                result["error"],
                "config file is empty; no BytePlus profiles are configured",
            )
            self.assertNotIn("Expecting value", json.dumps(result))

    def test_reports_malformed_config_without_parser_details(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text("{not-json", encoding="utf-8")
            path.chmod(0o600)
            result = doctor.inspect_profiles(path)
            self.assertEqual(result["state"], "malformed")
            self.assertEqual(
                result["error"],
                "config file is not valid JSON; no profiles were inspected",
            )
            self.assertNotIn("line 1 column", json.dumps(result))

    def test_parses_bp_service_table(self) -> None:
        help_text = """Usage: bp\n\nAvailable Commands:\n  Service            Description\n  -------            -----------\n  ecs                Compute\n  sts                Identity\n  login              Log in\n  mlplatform20240701 Machine learning\n\nFlags:\n  -h\n"""
        self.assertEqual(
            doctor.parse_bp_services(help_text), ["ecs", "mlplatform20240701", "sts"]
        )

    def test_failed_requested_auth_check_returns_nonzero(self) -> None:
        report = {
            "tools": {},
            "byteplus_config": {"path": "/isolated/config", "exists": False},
            "bp": {"service_count": 0},
            "auth_check": {"ok": False, "error": "expired"},
        }
        stdout = io.StringIO()
        with mock.patch.object(doctor, "build_report", return_value=report):
            with redirect_stdout(stdout):
                code = doctor.main(
                    [
                        "--check-auth",
                        "--profile",
                        "dev",
                        "--region",
                        "ap-southeast-1",
                        "--json",
                    ]
                )
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(stdout.getvalue())["auth_check"]["ok"])

    def test_identity_check_redacts_cli_output(self) -> None:
        command_result = {
            "ok": True,
            "trusted": True,
            "returncode": 0,
            "stdout": '{"AccountId":"123456789","AccessKeyId":"leak"}',
            "stderr": "",
        }
        with mock.patch.object(doctor, "run_command", return_value=command_result) as run:
            result = doctor.check_identity(
                "/opt/byteplus/bin/bp",
                profile="dev",
                region="ap-southeast-1",
                timeout=2,
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["identity"]["AccountId"], "***6789")
        self.assertEqual(result["identity"]["AccessKeyId"], "<redacted>")
        self.assertTrue(result["target_explicit"])
        self.assertTrue(run.call_args.kwargs["use_real_home"])

        with mock.patch.object(doctor, "run_command", return_value=command_result):
            detailed = doctor.check_identity(
                "/opt/byteplus/bin/bp",
                profile="dev",
                region="ap-southeast-1",
                timeout=2,
                show_identifiers=True,
            )
        self.assertEqual(detailed["identity"]["AccountId"], "123456789")
        self.assertEqual(detailed["identity"]["AccessKeyId"], "<redacted>")

    def test_subprocess_environment_drops_ambient_credentials(self) -> None:
        ambient = {
            "PATH": "/untrusted/bin",
            "BYTEPLUS_ACCESS_KEY": "secret-ak",
            "ARK_API_KEY": "secret-ark",
            "AWS_SECRET_ACCESS_KEY": "secret-aws",
            "LANG": "C.UTF-8",
        }
        executable = Path("opt") / "byteplus" / "bin" / "bp"
        home = Path("isolated-home")
        with mock.patch.dict(os.environ, ambient, clear=True):
            env = doctor.subprocess_env(str(executable), home)
        serialized = json.dumps(env)
        self.assertNotIn("secret-ak", serialized)
        self.assertNotIn("secret-ark", serialized)
        self.assertNotIn("secret-aws", serialized)
        self.assertEqual(env["HOME"], str(home))
        self.assertEqual(env["PATH"].split(os.pathsep)[0], str(executable.parent))

    def test_temporary_executable_is_rejected_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "bp"
            executable.write_text("fixture", encoding="utf-8")
            with mock.patch.object(doctor.subprocess, "run") as run:
                result = doctor.run_command([str(executable), "version"])
        self.assertFalse(result["ok"])
        self.assertFalse(result["trusted"])
        self.assertIn("temporary directory", result["error"])
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
