from __future__ import annotations

import base64
import hashlib
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
SCRIPT = ROOT / "skills" / "byteplus-cloud" / "scripts" / "seed_speech_smoke.py"
SPEC = importlib.util.spec_from_file_location("seed_speech_smoke", SCRIPT)
assert SPEC and SPEC.loader
seed_speech = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seed_speech)


MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x08smoke-mp3"


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.stream = io.BytesIO(body)
        self.status = status
        self.headers = headers or {}

    def read(self, size: int = -1) -> bytes:
        return self.stream.read(size)

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def encoded(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


class SeedSpeechSmokeTests(unittest.TestCase):
    def test_request_uses_current_fixed_contract_and_bounded_default_payload(self) -> None:
        secret = "secret-api-key-value"
        request = seed_speech.build_request(secret)
        headers = {key.lower(): value for key, value in request.header_items()}
        payload = json.loads(request.data)

        self.assertEqual(request.full_url, seed_speech.ENDPOINT)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(headers["content-type"], "application/json")
        self.assertEqual(headers["x-api-key"], secret)
        self.assertEqual(headers["x-api-resource-id"], "seed-tts-2.0")
        self.assertEqual(headers["x-api-app-key"], "aGjiRDfUWi")
        self.assertEqual(
            payload,
            {
                "req_params": {
                    "text": "Hi.",
                    "speaker": "en_male_tim_uranus_bigtts",
                    "audio_params": {"format": "mp3", "sample_rate": 24000},
                    "additions": '{"explicit_language":"en"}',
                }
            },
        )
        self.assertNotIn(secret, request.data.decode("utf-8"))

    def test_api_key_loads_from_owner_only_file_or_fixed_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "speech.key"
            key_file.write_text("file-secret\n", encoding="utf-8")
            key_file.chmod(0o600)
            self.assertEqual(
                seed_speech.load_api_key(
                    key_file, environ={seed_speech.API_KEY_ENV: "env-secret"}
                ),
                "file-secret",
            )
        self.assertEqual(
            seed_speech.load_api_key(
                None, environ={seed_speech.API_KEY_ENV: "env-secret"}
            ),
            "env-secret",
        )
        with self.assertRaises(seed_speech.SmokeError) as context:
            seed_speech.load_api_key(None, environ={})
        self.assertEqual(context.exception.error, "api_key_missing")

    @unittest.skipIf(os.name == "nt", "POSIX permission check")
    def test_api_key_file_rejects_group_or_world_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "speech.key"
            key_file.write_text("do-not-print-this", encoding="utf-8")
            key_file.chmod(0o644)
            with self.assertRaises(seed_speech.SmokeError) as context:
                seed_speech.load_api_key(key_file, environ={})
        self.assertEqual(context.exception.error, "api_key_file_permissions")
        self.assertNotIn("do-not-print-this", str(context.exception))

    def test_parser_accepts_one_json_response_and_returns_sanitized_evidence(self) -> None:
        body = json.dumps({"code": 20000000, "data": encoded(MP3)}).encode()
        result = seed_speech.evidence_from_response(body, log_id="safe-log-id")

        self.assertEqual(result["event"], "seed_speech_tts_succeeded")
        self.assertEqual(result["terminal_code"], 20000000)
        self.assertEqual(result["log_id"], "safe-log-id")
        self.assertEqual(result["audio_bytes"], len(MP3))
        self.assertEqual(result["audio_sha256"], hashlib.sha256(MP3).hexdigest())
        self.assertEqual(result["chunks"], 1)
        serialized = json.dumps(result)
        self.assertNotIn(encoded(MP3), serialized)
        self.assertNotIn("ID3", serialized)

    def test_parser_accepts_ndjson_chunks_and_requires_last_terminal_code(self) -> None:
        first, second = MP3[:8], MP3[8:]
        body = (
            json.dumps({"code": 10000000, "data": encoded(first)})
            + "\n"
            + json.dumps({"data": encoded(second)})
            + "\n"
            + json.dumps({"code": "20000000"})
        ).encode()
        result = seed_speech.evidence_from_response(body, log_id=None)
        self.assertEqual(result["audio_bytes"], len(MP3))
        self.assertEqual(result["chunks"], 2)

        unsuccessful = (
            json.dumps({"code": 20000000, "data": encoded(MP3)})
            + "\n"
            + json.dumps({"code": 55000000})
        ).encode()
        with self.assertRaises(seed_speech.SmokeError) as context:
            seed_speech.evidence_from_response(unsuccessful, log_id=None)
        self.assertEqual(context.exception.error, "terminal_code_missing_or_unsuccessful")
        self.assertEqual(context.exception.terminal_code, "55000000")

    def test_parser_accepts_sse_events_and_done_marker(self) -> None:
        first, second = MP3[:9], MP3[9:]
        body = (
            ": keepalive\n"
            "event: message\n"
            f"data: {json.dumps({'data': encoded(first)})}\n\n"
            f"data: {json.dumps({'data': encoded(second)})}\n\n"
            f"data: {json.dumps({'code': 20000000})}\n\n"
            "data: [DONE]\n"
        ).encode()
        result = seed_speech.evidence_from_response(body, log_id="request.123")
        self.assertEqual(result["audio_bytes"], len(MP3))
        self.assertEqual(result["chunks"], 2)
        self.assertEqual(result["log_id"], "request.123")

    def test_non_mp3_and_missing_terminal_code_are_rejected(self) -> None:
        not_mp3 = json.dumps(
            {"code": 20000000, "data": encoded(b"RIFFnot-an-mp3")}
        ).encode()
        with self.assertRaises(seed_speech.SmokeError) as context:
            seed_speech.evidence_from_response(not_mp3, log_id=None)
        self.assertEqual(context.exception.error, "audio_not_mp3")

        missing_code = json.dumps({"data": encoded(MP3)}).encode()
        with self.assertRaises(seed_speech.SmokeError) as context:
            seed_speech.evidence_from_response(missing_code, log_id=None)
        self.assertEqual(context.exception.error, "terminal_code_missing_or_unsuccessful")

    def test_run_smoke_never_returns_key_or_audio(self) -> None:
        secret = "top-secret-key-never-log"
        body = json.dumps({"code": 20000000, "audio_data": encoded(MP3)}).encode()
        captured_request = None

        def opener(request: object, *, timeout: float) -> FakeResponse:
            nonlocal captured_request
            captured_request = request
            self.assertEqual(timeout, 7)
            return FakeResponse(body, headers={"X-Tt-Logid": "log-safe-1"})

        result = seed_speech.run_smoke(secret, timeout=7, opener=opener)
        self.assertIsNotNone(captured_request)
        serialized = json.dumps(result)
        self.assertNotIn(secret, serialized)
        self.assertNotIn(encoded(MP3), serialized)
        self.assertEqual(result["log_id"], "log-safe-1")

    def test_cli_has_no_literal_api_key_option_and_failures_are_sanitized(self) -> None:
        parser = seed_speech.build_parser()
        option_strings = {
            option
            for action in parser._actions
            for option in action.option_strings
        }
        self.assertNotIn("--api-key", option_strings)
        self.assertIn("--api-key-file", option_strings)

        bad_stderr = io.StringIO()
        with redirect_stderr(bad_stderr):
            with self.assertRaises(SystemExit) as context:
                parser.parse_args(["--api-key", "secret-that-must-not-appear"])
        self.assertEqual(context.exception.code, 2)
        self.assertNotIn("secret-that-must-not-appear", bad_stderr.getvalue())

        secret = "secret-that-must-not-appear"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, {seed_speech.API_KEY_ENV: secret}, clear=True):
            with mock.patch.object(
                seed_speech,
                "run_smoke",
                side_effect=seed_speech.SmokeError("network_error"),
            ):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    status = seed_speech.main([])
        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn(secret, stderr.getvalue())
        self.assertEqual(
            json.loads(stderr.getvalue()),
            {"event": "seed_speech_tts_failed", "error": "network_error"},
        )


if __name__ == "__main__":
    unittest.main()
