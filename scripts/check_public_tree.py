#!/usr/bin/env python3
"""Reject private acceptance artifacts and common secrets from publishable files."""

from __future__ import annotations

import ipaddress
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROOTS = {
    ".byteplus",
    ".ruff_cache",
    ".terraform",
    "byteplus-cloud-workspace",
    "dist",
    "e2e",
}
FORBIDDEN_NAMES = {
    ".env",
    ".nest.json",
    "config.json",
    "known_hosts",
    "kubeconfig",
    "secrets.json",
}
FORBIDDEN_SUFFIXES = {
    ".7z",
    ".gz",
    ".har",
    ".jks",
    ".key",
    ".kubeconfig",
    ".log",
    ".p12",
    ".pem",
    ".pfx",
    ".skill",
    ".tar",
    ".tfplan",
    ".tfstate",
    ".zip",
}
ALLOWED_RUNTIME_TEMPLATES = {Path("skills/byteplus-cloud/assets/byteplus.project.yaml")}
SECRET_PATTERNS = {
    "BytePlus-style access key": re.compile(r"\bAKLT[A-Za-z0-9]{16,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:github_pat_|gh[opusr]_[A-Za-z0-9_]{20,})"),
    "AWS-style access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    "hard-coded bearer token": re.compile(r"(?i)authorization[\"']?\s*[:=]\s*[\"']Bearer [A-Za-z0-9._-]{20,}"),
    "signed URL": re.compile(r"(?i)[?&](?:X-Tos|X-Amz)-(?:Signature|Security-Token|Credential)="),
    "absolute user home": re.compile(r"/(?:Users|home)/[^/\s]+/"),
    "BytePlus resource identifier": re.compile(r"\b(?:eip|eni|kp|sg|subnet|vol|vpc|i)-[a-z0-9]{10,}\b"),
    "BytePlus request identifier": re.compile(r"\b20\d{6}[0-9A-F]{20,}(?:-[a-z0-9]+)?\b"),
    "private acceptance prefix": re.compile(r"\bbpskill-(?:e2e|cont)-20\d{6}-\d{6}\b"),
}
CONTENT_SCAN_EXEMPT = {Path("scripts/check_public_tree.py")}


def publishable_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode() for item in completed.stdout.split(b"\0") if item]


def check_path(path: Path) -> list[str]:
    relative = path.relative_to(ROOT)
    errors: list[str] = []
    if relative.parts and relative.parts[0] in FORBIDDEN_ROOTS:
        errors.append(f"forbidden private root: {relative}")
    if path.name in FORBIDDEN_NAMES:
        errors.append(f"forbidden sensitive filename: {relative}")
    if path.name.startswith(".env.") and path.name != ".env.example":
        errors.append(f"forbidden environment filename: {relative}")
    if path.name == "byteplus.project.yaml" and relative not in ALLOWED_RUNTIME_TEMPLATES:
        errors.append(f"forbidden runtime manifest: {relative}")
    if ".tfvars" in path.name:
        errors.append(f"forbidden Terraform variable file: {relative}")
    if path.name.startswith("kubeconfig"):
        errors.append(f"forbidden kubeconfig: {relative}")
    if any(path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        errors.append(f"forbidden sensitive suffix: {relative}")
    if path.is_symlink() and ROOT not in path.resolve().parents:
        errors.append(f"symlink escapes repository: {relative}")
    if path.is_file() and path.stat().st_size > 1_000_000:
        errors.append(f"unexpected file larger than 1 MB: {relative}")
    return errors


def check_content(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"unexpected binary or non-UTF-8 file: {path.relative_to(ROOT)}"]
    relative = path.relative_to(ROOT)
    if relative in CONTENT_SCAN_EXEMPT:
        return []
    errors = [
        f"{label} pattern in {relative}"
        for label, pattern in SECRET_PATTERNS.items()
        if pattern.search(text)
    ]
    documentation_networks = (
        ipaddress.ip_network("192.0.2.0/24"),
        ipaddress.ip_network("198.51.100.0/24"),
        ipaddress.ip_network("203.0.113.0/24"),
    )
    for match in re.finditer(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])", text):
        try:
            address = ipaddress.ip_address(match.group(0))
        except ValueError:
            continue
        if address.is_unspecified or address.is_loopback or any(address in network for network in documentation_networks):
            continue
        errors.append(f"non-documentation IP address in {relative}")
        break
    return errors


def main() -> int:
    errors: list[str] = []
    files = publishable_files()
    for path in files:
        errors.extend(check_path(path))
        if path.is_file():
            errors.extend(check_content(path))
    if errors:
        for error in sorted(set(errors)):
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"public tree check passed: {len(files)} publishable files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
