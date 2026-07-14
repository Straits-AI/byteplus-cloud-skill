#!/usr/bin/env python3
"""Export the installed BytePlus CLI help catalog as structured JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
BUILTIN_COMMANDS = {"completion", "configure", "login", "logout", "sso", "version"}


class CatalogError(RuntimeError):
    """Raised when the local CLI catalog cannot be inspected safely."""


@dataclass(frozen=True)
class CatalogEntry:
    name: str
    description: str = ""


@dataclass(frozen=True)
class Parameter:
    name: str
    type: str


def strip_ansi(value: str) -> str:
    return ANSI_ESCAPE.sub("", value).replace("\r\n", "\n")


def validate_identifier(value: str, label: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise CatalogError(f"invalid {label}: {value!r}")
    return value


def resolve_bp(explicit: Optional[str] = None) -> str:
    if explicit:
        is_path = (
            Path(explicit).is_absolute()
            or explicit.startswith("~")
            or "/" in explicit
            or "\\" in explicit
        )
        if is_path:
            path = Path(explicit).expanduser()
            if path.is_file() and os.access(path, os.X_OK):
                return str(path.resolve())
            raise CatalogError(f"bp executable path is not usable: {explicit}")
        resolved = shutil.which(explicit)
        if resolved:
            return resolved
        raise CatalogError(f"bp executable is not usable: {explicit}")
    resolved = shutil.which("bp")
    if not resolved:
        raise CatalogError("bp is not installed or is not on PATH")
    return resolved


def inspection_env(home: str) -> dict[str, str]:
    allowed = (
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "TMPDIR",
        "TMP",
        "TEMP",
    )
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env.update(
        {
            "HOME": home,
            "USERPROFILE": home,
            "LANG": "C",
            "LC_ALL": "C",
            "NO_COLOR": "1",
            "TERM": "dumb",
        }
    )
    return env


def run_help(bp_path: str, arguments: list[str], timeout: float = 10) -> str:
    try:
        with tempfile.TemporaryDirectory(prefix="bp-catalog-home-") as home:
            result = subprocess.run(
                [bp_path, *arguments, "--help"],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=inspection_env(home),
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CatalogError(f"unable to inspect bp help: {exc}") from exc
    output = strip_ansi(result.stdout or result.stderr)
    if result.returncode != 0:
        message = output.strip().splitlines()[-1] if output.strip() else "unknown error"
        raise CatalogError(f"bp {' '.join(arguments)} --help failed: {message}")
    return output


def run_version(bp_path: str, timeout: float = 10) -> str:
    try:
        with tempfile.TemporaryDirectory(prefix="bp-catalog-home-") as home:
            result = subprocess.run(
                [bp_path, "version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=inspection_env(home),
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CatalogError(f"unable to inspect bp version: {exc}") from exc
    output = strip_ansi(result.stdout or result.stderr).strip()
    if result.returncode != 0:
        raise CatalogError(f"bp version failed: {output or 'unknown error'}")
    return output


def parse_entries(text: str, heading: str) -> list[CatalogEntry]:
    lines = strip_ansi(text).splitlines()
    try:
        start = next(
            index for index, line in enumerate(lines) if line.strip() == heading
        )
    except StopIteration:
        raise CatalogError(f"bp help did not contain {heading!r}") from None

    entries: list[CatalogEntry] = []
    saw_separator = False
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not saw_separator:
            if stripped.startswith("------"):
                saw_separator = True
            continue
        if not stripped:
            continue
        if stripped.startswith(("Flags:", "Fixed Flags:", "Examples:", 'Use "')):
            break
        match = re.match(r"^\s{2}([A-Za-z][A-Za-z0-9_-]*)(?:\s+(.*?))?\s*$", line)
        if match:
            entries.append(CatalogEntry(match.group(1), (match.group(2) or "").strip()))
    if not entries:
        raise CatalogError(f"bp help contained no entries below {heading!r}")
    return entries


def parse_parameters(text: str) -> list[Parameter]:
    lines = strip_ansi(text).splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if line.strip() == "Available Parameters:"
        )
    except StopIteration:
        return []

    parameters: list[Parameter] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("Fixed Flags:"):
            break
        match = re.match(r"^\s{2}(--[A-Za-z0-9_.-]+)\s+([^\s]+)\s*$", line)
        if match:
            parameters.append(Parameter(name=match.group(1)[2:], type=match.group(2)))
    return parameters


def parse_fixed_flags(text: str) -> list[Parameter]:
    lines = strip_ansi(text).splitlines()
    try:
        start = next(
            index for index, line in enumerate(lines) if line.strip() == "Fixed Flags:"
        )
    except StopIteration:
        return []

    flags: list[Parameter] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("Examples:", 'Use "')):
            break
        match = re.match(r"^\s{2}(---[A-Za-z0-9_-]+)(?:\s+([^\s]+))?", line)
        if match:
            flags.append(
                Parameter(name=match.group(1), type=match.group(2) or "boolean")
            )
    return flags


def parse_usage(text: str) -> str:
    lines = strip_ansi(text).splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("Usage:"):
            continue
        inline = stripped.removeprefix("Usage:").strip()
        if inline:
            return inline
        for candidate in lines[index + 1 :]:
            if candidate.strip():
                return candidate.strip()
    return ""


def catalog_services(bp_path: str, timeout: float) -> list[dict[str, str]]:
    return [
        {
            **asdict(entry),
            "kind": "builtin" if entry.name in BUILTIN_COMMANDS else "service",
        }
        for entry in parse_entries(
            run_help(bp_path, [], timeout), "Available Commands:"
        )
    ]


def catalog_actions(bp_path: str, service: str, timeout: float) -> list[dict[str, str]]:
    validate_identifier(service, "service")
    return [
        asdict(entry)
        for entry in parse_entries(
            run_help(bp_path, [service], timeout),
            "Available Actions:",
        )
    ]


def describe_action(
    bp_path: str, service: str, action: str, timeout: float
) -> dict[str, Any]:
    validate_identifier(service, "service")
    validate_identifier(action, "action")
    help_text = run_help(bp_path, [service, action], timeout)
    return {
        "service": service,
        "action": action,
        "usage": parse_usage(help_text),
        "parameters": [asdict(item) for item in parse_parameters(help_text)],
        "fixed_flags": [asdict(item) for item in parse_fixed_flags(help_text)],
        "metadata_limitations": [
            "required fields are not reliably marked by bp help",
            "enum values, IAM permissions, side effects, regions, quotas, and pricing require current official documentation",
        ],
    }


def find_entries(
    bp_path: str,
    query: str,
    *,
    service: Optional[str],
    timeout: float,
) -> dict[str, Any]:
    needle = query.casefold().strip()
    if not needle:
        raise CatalogError("query must not be empty")
    services = catalog_services(bp_path, timeout)
    service_matches = [
        item
        for item in services
        if needle in item["name"].casefold() or needle in item["description"].casefold()
    ]
    candidates = (
        [service]
        if service
        else [item["name"] for item in services if item["kind"] == "service"]
    )
    action_matches: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    for candidate in candidates:
        validate_identifier(candidate, "service")
        try:
            actions = catalog_actions(bp_path, candidate, timeout)
        except CatalogError as exc:
            errors.append({"service": candidate, "error": str(exc)})
            continue
        for action in actions:
            if (
                needle in action["name"].casefold()
                or needle in action["description"].casefold()
            ):
                action_matches.append({"service": candidate, **action})
    return {
        "query": query,
        "service_matches": service_matches,
        "action_matches": action_matches,
        "errors": errors,
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bp", help="Path or command name for the bp executable.")
    parser.add_argument(
        "--timeout", type=float, default=10, help="Per-help-call timeout."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "services", help="List installed services and built-in commands."
    )
    actions = subparsers.add_parser("actions", help="List actions for one service.")
    actions.add_argument("service")
    describe = subparsers.add_parser(
        "describe", help="Describe one action's CLI parameters."
    )
    describe.add_argument("service")
    describe.add_argument("action")
    find = subparsers.add_parser("find", help="Search installed service/action names.")
    find.add_argument("query")
    find.add_argument("--service", help="Restrict action search to one service.")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        bp_path = resolve_bp(args.bp)
        if args.command == "services":
            entries = catalog_services(bp_path, args.timeout)
            payload: dict[str, Any] = {
                "version": run_version(bp_path, args.timeout),
                "service_count": sum(item["kind"] == "service" for item in entries),
                "entries": entries,
            }
        elif args.command == "actions":
            entries = catalog_actions(bp_path, args.service, args.timeout)
            payload = {
                "service": args.service,
                "action_count": len(entries),
                "actions": entries,
            }
        elif args.command == "describe":
            payload = describe_action(bp_path, args.service, args.action, args.timeout)
        else:
            payload = find_entries(
                bp_path,
                args.query,
                service=args.service,
                timeout=args.timeout,
            )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except CatalogError as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
