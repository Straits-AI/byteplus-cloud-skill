#!/usr/bin/env python3
"""Run one bounded Seed Speech TTS 2.0 smoke test without exposing secrets/audio."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINT = "https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/unidirectional"
RESOURCE_ID = "seed-tts-2.0"
APP_KEY = "aGjiRDfUWi"
SPEAKER = "en_male_tim_uranus_bigtts"
API_KEY_ENV = "BYTEPLUS_SPEECH_API_KEY"
SUCCESS_CODE = 20_000_000
MAX_TEXT_CHARS = 80
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
MAX_MESSAGES = 10_000
_AUDIO_KEYS = {"audio", "audio_data", "audiodata", "data", "payload"}


class SmokeError(Exception):
    """A deliberately sanitized smoke-test failure."""

    def __init__(
        self,
        error: str,
        *,
        http_status: Optional[int] = None,
        terminal_code: Optional[str] = None,
        log_id: Optional[str] = None,
    ) -> None:
        super().__init__(error)
        self.error = error
        self.http_status = http_status
        self.terminal_code = terminal_code
        self.log_id = log_id

    def evidence(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "event": "seed_speech_tts_failed",
            "error": self.error,
        }
        if self.http_status is not None:
            result["http_status"] = self.http_status
        if self.terminal_code is not None:
            result["terminal_code"] = self.terminal_code
        if self.log_id is not None:
            result["log_id"] = self.log_id
        return result


class SanitizedArgumentParser(argparse.ArgumentParser):
    """Reject invalid arguments without reflecting command-line values."""

    def error(self, message: str) -> None:
        del message
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: invalid arguments\n")


def _validate_api_key(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise SmokeError("api_key_missing")
    if len(candidate) > 16_384:
        raise SmokeError("api_key_invalid")
    if any(character.isspace() or ord(character) < 0x20 for character in candidate):
        raise SmokeError("api_key_invalid")
    return candidate


def load_api_key(
    api_key_file: Optional[Path],
    *,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    """Load a key from a protected file or fixed environment variable."""

    source = os.environ if environ is None else environ
    if api_key_file is None:
        return _validate_api_key(source.get(API_KEY_ENV, ""))

    path = api_key_file.expanduser()
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise SmokeError("api_key_file_unreadable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise SmokeError("api_key_file_invalid")
    if os.name != "nt" and stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SmokeError("api_key_file_permissions")
    if metadata.st_size > 16_384:
        raise SmokeError("api_key_file_invalid")
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SmokeError("api_key_file_unreadable") from exc
    return _validate_api_key(value)


def validate_text(value: str) -> str:
    if not value or len(value) > MAX_TEXT_CHARS:
        raise SmokeError("text_must_be_1_to_80_characters")
    if any(ord(character) < 0x20 and character not in "\t\n" for character in value):
        raise SmokeError("text_contains_control_characters")
    return value


def build_request(api_key: str, *, text: str = "Hi.") -> Request:
    payload = {
        "req_params": {
            "text": validate_text(text),
            "speaker": SPEAKER,
            "audio_params": {"format": "mp3", "sample_rate": 24_000},
            "additions": json.dumps(
                {"explicit_language": "en"}, separators=(",", ":")
            ),
        }
    }
    return Request(
        ENDPOINT,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": _validate_api_key(api_key),
            "X-Api-Resource-Id": RESOURCE_ID,
            "X-Api-App-Key": APP_KEY,
        },
        method="POST",
    )


def _flatten_messages(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_messages(item)
    else:
        raise SmokeError("response_json_not_an_object")


def _decode_json_sequence(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    messages: list[dict[str, Any]] = []
    offset = 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset >= len(text):
            break
        try:
            value, offset = decoder.raw_decode(text, offset)
        except json.JSONDecodeError as exc:
            raise SmokeError("response_json_invalid") from exc
        messages.extend(_flatten_messages(value))
        if len(messages) > MAX_MESSAGES:
            raise SmokeError("response_has_too_many_messages")
    return messages


def parse_messages(raw: bytes) -> list[dict[str, Any]]:
    """Parse a single JSON value, concatenated/NDJSON values, or SSE data events."""

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SmokeError("response_not_utf8_json") from exc
    if not text.strip():
        raise SmokeError("response_empty")

    lines = text.splitlines()
    if not any(line.lstrip().startswith("data:") for line in lines):
        return _decode_json_sequence(text)

    # Each SSE event can contain one or more data lines. Joining event payloads
    # with newlines handles both pretty JSON and servers that omit blank event
    # separators and emit one complete JSON object per data line.
    payload_parts: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("data:"):
            payload = stripped[5:].lstrip()
            if payload and payload != "[DONE]":
                payload_parts.append(payload)
            continue
        if not stripped or stripped.startswith((":", "event:", "id:", "retry:")):
            continue
        raise SmokeError("response_sse_invalid")
    if not payload_parts:
        raise SmokeError("response_empty")
    return _decode_json_sequence("\n".join(payload_parts))


def _decode_audio_value(value: str) -> Optional[bytes]:
    compact = "".join(value.split())
    if not compact:
        return None
    padded = compact + "=" * (-len(compact) % 4)
    try:
        decoded = base64.b64decode(padded, validate=True)
    except (ValueError, binascii.Error):
        return None
    return decoded or None


def _audio_chunks(value: Any, *, parent_key: str = "") -> Iterable[bytes]:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _AUDIO_KEYS and isinstance(child, str):
                decoded = _decode_audio_value(child)
                if decoded is not None:
                    yield decoded
            elif isinstance(child, (dict, list)):
                yield from _audio_chunks(child, parent_key=normalized)
    elif isinstance(value, list):
        for child in value:
            yield from _audio_chunks(child, parent_key=parent_key)


def _safe_terminal_code(value: Any) -> Optional[str]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and 1 <= len(value) <= 32:
        if all(character.isalnum() or character in "._-" for character in value):
            return value
    return None


def _safe_log_id(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        return None
    if not all(character.isalnum() or character in "._:-" for character in value):
        return None
    return value


def _response_log_id(response: Any) -> Optional[str]:
    headers = getattr(response, "headers", None)
    value = headers.get("X-Tt-Logid") if headers is not None else None
    if value is None and hasattr(response, "getheader"):
        value = response.getheader("X-Tt-Logid")
    return _safe_log_id(value)


def _read_response(response: Any) -> bytes:
    pieces: list[bytes] = []
    total = 0
    while True:
        piece = response.read(READ_CHUNK_BYTES)
        if not piece:
            break
        if not isinstance(piece, bytes):
            raise SmokeError("response_not_bytes")
        total += len(piece)
        if total > MAX_RESPONSE_BYTES:
            raise SmokeError("response_too_large")
        pieces.append(piece)
    return b"".join(pieces)


def _is_mp3(value: bytes) -> bool:
    if value.startswith(b"ID3"):
        return True
    return len(value) >= 2 and value[0] == 0xFF and value[1] & 0xE0 == 0xE0


def evidence_from_response(raw: bytes, *, log_id: Optional[str]) -> dict[str, Any]:
    messages = parse_messages(raw)
    chunks: list[bytes] = []
    last_code: Optional[str] = None
    for message in messages:
        if "code" in message:
            safe_code = _safe_terminal_code(message["code"])
            if safe_code is None:
                raise SmokeError("terminal_code_invalid", log_id=log_id)
            last_code = safe_code
        chunks.extend(_audio_chunks(message))

    if last_code != str(SUCCESS_CODE):
        raise SmokeError(
            "terminal_code_missing_or_unsuccessful",
            terminal_code=last_code,
            log_id=log_id,
        )
    audio = b"".join(chunks)
    if not audio:
        raise SmokeError("audio_missing", terminal_code=last_code, log_id=log_id)
    if not _is_mp3(audio):
        raise SmokeError("audio_not_mp3", terminal_code=last_code, log_id=log_id)
    return {
        "event": "seed_speech_tts_succeeded",
        "terminal_code": SUCCESS_CODE,
        "log_id": log_id,
        "audio_bytes": len(audio),
        "audio_sha256": hashlib.sha256(audio).hexdigest(),
        "chunks": len(chunks),
    }


def run_smoke(
    api_key: str,
    *,
    text: str = "Hi.",
    timeout: float = 30.0,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    request = build_request(api_key, text=text)
    try:
        with opener(request, timeout=timeout) as response:
            log_id = _response_log_id(response)
            status = getattr(response, "status", None)
            if status is None and hasattr(response, "getcode"):
                status = response.getcode()
            if status is not None and not 200 <= int(status) < 300:
                raise SmokeError("http_error", http_status=int(status), log_id=log_id)
            raw = _read_response(response)
    except SmokeError:
        raise
    except HTTPError as exc:
        raise SmokeError(
            "http_error",
            http_status=exc.code,
            log_id=_safe_log_id(exc.headers.get("X-Tt-Logid") if exc.headers else None),
        ) from exc
    except (OSError, URLError, TimeoutError) as exc:
        raise SmokeError("network_error") from exc
    return evidence_from_response(raw, log_id=log_id)


def build_parser() -> argparse.ArgumentParser:
    parser = SanitizedArgumentParser(
        description=(
            "Synthesize one bounded Seed Speech TTS 2.0 phrase and emit only "
            "sanitized verification evidence."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        help=(
            "owner-only file containing the API key; otherwise read "
            f"{API_KEY_ENV}"
        ),
    )
    parser.add_argument("--text", default="Hi.", help="smoke phrase (1-80 characters)")
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if not 0 < args.timeout <= 120:
            raise SmokeError("timeout_must_be_between_0_and_120_seconds")
        api_key = load_api_key(args.api_key_file)
        result = run_smoke(api_key, text=args.text, timeout=args.timeout)
    except SmokeError as exc:
        print(json.dumps(exc.evidence(), sort_keys=True), file=sys.stderr)
        return 1
    except Exception:
        # Never serialize arbitrary exception text: library/network errors can
        # reflect request headers or response bodies.
        print(
            json.dumps(
                {"event": "seed_speech_tts_failed", "error": "unexpected_error"},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
