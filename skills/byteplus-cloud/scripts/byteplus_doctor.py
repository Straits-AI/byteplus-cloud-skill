#!/usr/bin/env python3
"""Report BytePlus deployment prerequisites without exposing local credentials."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

SENSITIVE_KEY = re.compile(
    r"(?:access.?key|secret|session.?token|security.?token|refresh.?token|"
    r"access.?token|password|credential|authorization|private.?key|api.?key|"
    r"signature|signed.?url|cookie|passphrase)",
    re.IGNORECASE,
)
SENSITIVE_LABEL = (
    r"(?:access[_-]?key(?:[_-]?id)?|secret(?:[_-]?(?:access)?[_-]?key)?|"
    r"(?:session|security|access|refresh)[_-]?token|authorization|password|"
    r"private[_-]?key|api[_-]?key|signature|signed[_-]?url|cookie|passphrase)"
)
PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?"
    r"(?:-----END [A-Z0-9 ]*PRIVATE KEY-----|$)",
    re.IGNORECASE | re.DOTALL,
)
AUTHORIZATION_LINE = re.compile(r"(?i)((?:proxy[_-]?)?authorization\s*[=:]\s*)[^\r\n]*")
COOKIE_LINE = re.compile(r"(?i)((?:set[_-]?)?cookie\s*[=:]\s*)[^\r\n]*")
BEARER_TOKEN = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+")
BP_BUILTIN_COMMANDS = {"completion", "configure", "login", "logout", "sso", "version"}
IDENTIFIER_KEY = re.compile(r"(?:account|owner|principal|user).?id$|^(?:arn|trn)$", re.IGNORECASE)
SAFE_ENV_KEYS = {
    "COMSPEC",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATHEXT",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SYSTEMROOT",
    "SystemRoot",
    "WINDIR",
}
TEXT_REDACTIONS = [
    (
        re.compile(
            rf"(?i)([\"']?{SENSITIVE_LABEL}[\"']?\s*[=:]\s*)"
            r"(?:[\"'][^\"'\r\n]*[\"']|[^\s,}\]&]+)"
        ),
        r'\1"<redacted>"',
    ),
    (
        re.compile(
            r"(?i)([?&](?:X-Tos-(?:Credential|Signature|Security-Token)|"
            r"X-Amz-(?:Credential|Signature|Security-Token))=)[^&\s]+"
        ),
        r"\1<redacted>",
    ),
]


def redact_text(value: str, limit: int = 8000) -> str:
    result = value[:limit]
    home = str(Path.home())
    if home and home != os.sep:
        result = result.replace(home, "~")
    result = PRIVATE_KEY_BLOCK.sub("<redacted-private-key>", result)
    result = AUTHORIZATION_LINE.sub(r'\1"<redacted>"', result)
    result = COOKIE_LINE.sub(r'\1"<redacted>"', result)
    result = BEARER_TOKEN.sub(r"\1<redacted>", result)
    for pattern, replacement in TEXT_REDACTIONS:
        result = pattern.sub(replacement, result)
    return result


def redact_value(value: Any, key: str = "") -> Any:
    if SENSITIVE_KEY.search(key):
        return "<redacted>"
    if isinstance(value, dict):
        return {str(k): redact_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def untrusted_executable_reason(executable: str, workspace: Optional[Path] = None) -> Optional[str]:
    path = Path(executable).expanduser()
    if not path.is_absolute():
        return "resolved command is not an absolute path"
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return "resolved command does not exist"
    if not resolved.is_file():
        return "resolved command is not a regular file"

    temp_roots = {Path(tempfile.gettempdir()).resolve(), Path("/tmp"), Path("/private/tmp")}
    if any(root.exists() and _is_within(resolved, root) for root in temp_roots):
        return "resolved command is under an operating-system temporary directory"

    project = (workspace or Path.cwd()).resolve()
    if project != Path.home().resolve() and _is_within(resolved, project):
        return "resolved command is inside the current workspace"
    return None


def subprocess_env(executable: str, home: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key in SAFE_ENV_KEYS}
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["PATH"] = os.pathsep.join((str(Path(executable).parent), os.defpath))
    temp = tempfile.gettempdir()
    env["TMPDIR"] = temp
    env["TEMP"] = temp
    env["TMP"] = temp
    return env


def run_command(
    command: list[str],
    timeout: float = 10,
    *,
    use_real_home: bool = False,
) -> dict[str, Any]:
    if not command:
        return {"ok": False, "error": "empty command"}
    reason = untrusted_executable_reason(command[0])
    if reason:
        return {"ok": False, "error": reason, "trusted": False}

    try:
        with tempfile.TemporaryDirectory(prefix="byteplus-doctor-home-") as temporary:
            home = Path.home() if use_real_home else Path(temporary)
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=subprocess_env(command[0], home),
            )
        return {
            "ok": result.returncode == 0,
            "trusted": True,
            "returncode": result.returncode,
            "stdout": redact_text(result.stdout.strip()),
            "stderr": redact_text(result.stderr.strip()),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {timeout:g}s"}
    except OSError as exc:
        return {"ok": False, "error": redact_text(str(exc))}


TOOL_COMMANDS: dict[str, list[str]] = {
    "bp": ["version"],
    "terraform": ["version", "-json"],
    "tofu": ["version", "-json"],
    "node": ["--version"],
    "npm": ["--version"],
    "npx": ["--version"],
    "nest": ["--version"],
    "docker": ["--version"],
    "kubectl": ["version", "--client", "--output=json"],
    "helm": ["version", "--short"],
    "git": ["--version"],
}


def inspect_tools(timeout: float = 10) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for name, arguments in TOOL_COMMANDS.items():
        executable = shutil.which(name)
        if not executable:
            report[name] = {"installed": False}
            continue
        reason = untrusted_executable_reason(executable)
        if reason:
            report[name] = {
                "installed": True,
                "trusted": False,
                "path": executable,
                "error": reason,
            }
            continue
        result = run_command([executable, *arguments], timeout=timeout)
        report[name] = {
            "installed": True,
            "trusted": result.get("trusted", False),
            "path": executable,
            "version_check": result,
        }
    return report


def config_permissions(path: Path) -> dict[str, Any]:
    mode = stat.S_IMODE(path.stat().st_mode)
    return {
        "octal": f"{mode:04o}",
        "owner_only": mode & 0o077 == 0,
    }


def inspect_profiles(path: Optional[Path] = None, *, show_identifiers: bool = False) -> dict[str, Any]:
    config_path = (path or Path.home() / ".byteplus" / "config.json").expanduser()
    result: dict[str, Any] = {
        "path": str(config_path),
        "exists": config_path.is_file(),
        "state": "missing",
    }
    if not config_path.is_file():
        return result

    try:
        result["permissions"] = config_permissions(config_path)
        contents = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        result["state"] = "unreadable"
        result["error"] = redact_text(str(exc))
        return result

    if not contents.strip():
        result["state"] = "empty"
        result["error"] = "config file is empty; no BytePlus profiles are configured"
        return result

    try:
        config = json.loads(contents)
    except json.JSONDecodeError:
        result["state"] = "malformed"
        result["error"] = "config file is not valid JSON; no profiles were inspected"
        return result

    if not isinstance(config, dict):
        result["state"] = "malformed"
        result["error"] = "config root is not a JSON object"
        return result

    result["state"] = "valid"
    current = config.get("current")
    profiles = config.get("profiles", {})
    sanitized_profiles: list[dict[str, Any]] = []
    if isinstance(profiles, dict):
        for index, name in enumerate(sorted(profiles), start=1):
            raw = profiles[name]
            if not isinstance(raw, dict):
                continue
            sanitized_profiles.append(
                {
                    "name": str(name) if show_identifiers else f"<profile-{index}>",
                    "current": name == current,
                    "mode": raw.get("mode") or "ak",
                    "region": raw.get("region") or "",
                    "sso_session": (
                        raw.get("sso-session")
                        or raw.get("sso_session")
                        or raw.get("sso-session-name")
                        or ""
                    )
                    if show_identifiers
                    else ("<configured>" if any(raw.get(key) for key in ("sso-session", "sso_session", "sso-session-name")) else ""),
                }
            )
    result["current"] = (
        current if show_identifiers and isinstance(current, str) else "<configured>" if isinstance(current, str) else ""
    )
    result["profiles"] = redact_value(sanitized_profiles)
    result["profile_count"] = len(sanitized_profiles)
    return result


def parse_bp_services(help_text: str) -> list[str]:
    services: list[str] = []
    in_table = False
    for line in help_text.splitlines():
        if line.strip().startswith("-------"):
            in_table = True
            continue
        if in_table and (line.startswith("Flags:") or line.startswith("Fixed Flags:")):
            break
        if not in_table:
            continue
        match = re.match(r"^\s{2}([A-Za-z][A-Za-z0-9_-]*)\s+", line)
        if match:
            services.append(match.group(1))
    return sorted(set(services) - BP_BUILTIN_COMMANDS)


def inspect_bp(tools: dict[str, Any], timeout: float) -> dict[str, Any]:
    entry = tools.get("bp", {})
    if not entry.get("installed"):
        return {"installed": False, "services": []}
    if not entry.get("trusted"):
        return {
            "installed": True,
            "trusted": False,
            "services": [],
            "error": entry.get("error") or "bp executable is not trusted",
        }
    executable = str(entry["path"])
    help_result = run_command([executable, "--help"], timeout=timeout)
    services = parse_bp_services(str(help_result.get("stdout", "")))
    return {
        "installed": True,
        "trusted": help_result.get("trusted", False),
        "path": executable,
        "services": services,
        "service_count": len(services),
        "help_ok": help_result.get("ok", False),
    }


def check_identity(
    bp_path: str,
    *,
    profile: str,
    region: str,
    timeout: float,
    show_identifiers: bool = False,
) -> dict[str, Any]:
    command = [
        bp_path,
        "sts",
        "GetCallerIdentity",
        "---profile",
        profile,
        "---region",
        region,
    ]
    result = dict(run_command(command, timeout=timeout, use_real_home=True))
    stdout = result.get("stdout")
    if isinstance(stdout, str) and stdout:
        try:
            identity = redact_value(json.loads(stdout))
            result["identity"] = identity if show_identifiers else mask_identity(identity)
            result.pop("stdout", None)
        except json.JSONDecodeError:
            pass
    result["target_explicit"] = True
    result["note"] = (
        "This is a read-only STS API call, but the CLI may refresh and cache temporary "
        "OAuth/SSO credentials as part of normal authentication."
    )
    return result


def mask_identifier(value: str) -> str:
    suffix = value[-4:] if len(value) >= 4 else value
    return f"***{suffix}" if suffix else "<masked>"


def mask_identity(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        return {str(item_key): mask_identity(item, str(item_key)) for item_key, item in value.items()}
    if isinstance(value, list):
        return [mask_identity(item, key) for item in value]
    if isinstance(value, str) and IDENTIFIER_KEY.search(key):
        return mask_identifier(value)
    return value


def mask_local_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): (f"<local>/{Path(item).name}" if str(key) == "path" and isinstance(item, str) else mask_local_paths(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [mask_local_paths(item) for item in value]
    return value


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    tools = inspect_tools(timeout=args.timeout)
    report: dict[str, Any] = {
        "tools": tools,
        "byteplus_config": inspect_profiles(
            Path(args.config) if args.config else None,
            show_identifiers=args.show_identifiers,
        ),
        "bp": inspect_bp(tools, args.timeout),
        "target": {
            "profile": args.profile if args.show_identifiers and args.profile else "<configured>" if args.profile else "",
            "region": args.region or "",
            "explicit": bool(args.profile and args.region),
        },
    }
    if args.check_auth:
        if report["bp"].get("installed"):
            assert args.profile and args.region
            report["auth_check"] = check_identity(
                str(report["bp"]["path"]),
                profile=args.profile,
                region=args.region,
                timeout=args.timeout,
                show_identifiers=args.show_identifiers,
            )
        else:
            report["auth_check"] = {"ok": False, "error": "bp is not installed"}
    sanitized = redact_value(report)
    return sanitized if args.show_local_metadata else mask_local_paths(sanitized)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect BytePlus deployment tooling and sanitized profile metadata."
    )
    parser.add_argument("--profile", help="Profile for an optional identity check.")
    parser.add_argument("--region", help="Region for an optional identity check.")
    parser.add_argument(
        "--check-auth",
        action="store_true",
        help="Run the read-only STS GetCallerIdentity call.",
    )
    parser.add_argument(
        "--config",
        help="Alternative BytePlus CLI config path; defaults to ~/.byteplus/config.json.",
    )
    parser.add_argument(
        "--timeout", type=float, default=10, help="Per-command timeout."
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit JSON (default is a summary)."
    )
    parser.add_argument(
        "--show-identifiers",
        action="store_true",
        help="Show non-secret profile/session names and full identity identifiers.",
    )
    parser.add_argument(
        "--show-local-metadata",
        action="store_true",
        help="Show sanitized local tool and config paths instead of masking them.",
    )
    args = parser.parse_args(argv)
    if args.check_auth and not (args.profile and args.region):
        parser.error("--check-auth requires both --profile and --region")
    return args


def print_summary(report: dict[str, Any]) -> None:
    print("BytePlus deployment doctor")
    print("Tools:")
    for name, details in report["tools"].items():
        status = "found" if details.get("installed") else "missing"
        suffix = f" ({details.get('path')})" if details.get("path") else ""
        print(f"  {name}: {status}{suffix}")
    config = report["byteplus_config"]
    print(
        f"Config: {'found' if config.get('exists') else 'missing'} ({config['path']})"
    )
    if config.get("exists"):
        print(f"Config state: {config.get('state', 'unknown')}")
        if config.get("error"):
            print(f"Config diagnostic: {config['error']}")
        print(
            f"Profiles: {config.get('profile_count', 0)}; current={config.get('current') or '<none>'}"
        )
        permissions = config.get("permissions", {})
        if permissions and not permissions.get("owner_only"):
            print(
                f"Warning: config permissions are {permissions.get('octal')}, not owner-only"
            )
    print(f"bp catalog entries: {report['bp'].get('service_count', 0)}")
    if "auth_check" in report:
        print(f"Auth check: {'ok' if report['auth_check'].get('ok') else 'failed'}")


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_summary(report)
    if args.check_auth and not report.get("auth_check", {}).get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
