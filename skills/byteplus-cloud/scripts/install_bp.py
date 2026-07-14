#!/usr/bin/env python3
"""Install an official BytePlus CLI release after verifying release integrity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Optional

API_ROOT = "https://api.github.com/repos/byteplus-sdk/byteplus-cli"
REPOSITORY_ROOT = "https://github.com/byteplus-sdk/byteplus-cli"
RELEASE_DOWNLOAD_PREFIX = (
    "https://github.com/byteplus-sdk/byteplus-cli/releases/download/"
)
USER_AGENT = "byteplus-cloud-skill-installer/1"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
MAX_BINARY_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 4096
MAX_EXPANDED_BYTES = 256 * 1024 * 1024


class InstallerError(RuntimeError):
    """Raised for an expected, user-actionable installer failure."""


@dataclass(frozen=True)
class InstallPlan:
    version: str
    tag: str
    system: str
    architecture: str
    archive_name: str
    archive_url: str
    checksum_name: str
    checksum_url: str
    destination: str


def normalize_system(value: Optional[str] = None) -> str:
    raw = (value or platform.system()).strip().lower()
    mapping = {
        "darwin": "darwin",
        "linux": "linux",
        "freebsd": "freebsd",
        "windows": "windows",
        "win32": "windows",
    }
    try:
        return mapping[raw]
    except KeyError as exc:
        raise InstallerError(f"unsupported operating system: {raw}") from exc


def normalize_architecture(value: Optional[str] = None) -> str:
    raw = (value or platform.machine()).strip().lower()
    mapping = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "i386": "386",
        "i686": "386",
        "x86": "386",
        "armv7": "arm",
        "armv7l": "arm",
        "arm": "arm",
    }
    try:
        return mapping[raw]
    except KeyError as exc:
        raise InstallerError(f"unsupported CPU architecture: {raw}") from exc


def release_api_url(version: str) -> str:
    if version == "latest":
        return f"{API_ROOT}/releases/latest"
    tag = version if version.startswith("v") else f"v{version}"
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", tag):
        raise InstallerError(f"invalid release version: {version}")
    return f"{API_ROOT}/releases/tags/{tag}"


def synthetic_release(
    tag: str,
    *,
    system: Optional[str] = None,
    architecture: Optional[str] = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", tag):
        raise InstallerError(f"invalid release tag: {tag}")
    version = tag[1:]
    os_name = normalize_system(system)
    arch = normalize_architecture(architecture)
    extension = ".zip" if os_name == "windows" else ".tar.gz"
    archive_name = f"byteplus-cli_{version}_{os_name}_{arch}{extension}"
    checksum_name = f"byteplus-cli_{version}_SHA256SUMS"
    base = f"{RELEASE_DOWNLOAD_PREFIX}{tag}/"
    return {
        "tag_name": tag,
        "assets": [
            {"name": archive_name, "browser_download_url": base + archive_name},
            {"name": checksum_name, "browser_download_url": base + checksum_name},
        ],
    }


def resolve_latest_tag(timeout: float = 30) -> str:
    request = urllib.request.Request(
        f"{REPOSITORY_ROOT}/releases/latest",
        headers={"Accept": "text/html", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        raise InstallerError(
            f"HTTP {exc.code} while resolving the latest release"
        ) from exc
    except urllib.error.URLError as exc:
        raise InstallerError(
            f"unable to resolve the latest release: {exc.reason}"
        ) from exc
    prefix = f"{REPOSITORY_ROOT}/releases/tag/"
    if not final_url.startswith(prefix):
        raise InstallerError(f"unexpected latest-release redirect: {final_url}")
    tag = final_url[len(prefix) :].split("?", 1)[0].rstrip("/")
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", tag):
        raise InstallerError(f"latest-release redirect has an invalid tag: {tag}")
    return tag


def resolve_release(version: str, timeout: float = 30) -> dict[str, Any]:
    if version != "latest":
        api_url = release_api_url(version)
        tag = api_url.rsplit("/", 1)[-1]
        return synthetic_release(tag)
    try:
        return fetch_json(release_api_url("latest"), timeout=timeout)
    except InstallerError:
        return synthetic_release(resolve_latest_tag(timeout))


def fetch_bytes(
    url: str, *, timeout: float = 30, limit: int = MAX_DOWNLOAD_BYTES
) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > limit:
                raise InstallerError(f"download exceeds {limit} bytes: {url}")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    raise InstallerError(f"download exceeds {limit} bytes: {url}")
                chunks.append(chunk)
            return b"".join(chunks)
    except urllib.error.HTTPError as exc:
        raise InstallerError(f"HTTP {exc.code} while retrieving {url}") from exc
    except urllib.error.URLError as exc:
        raise InstallerError(f"unable to retrieve {url}: {exc.reason}") from exc


def fetch_json(url: str, *, timeout: float = 30) -> dict[str, Any]:
    try:
        value = json.loads(fetch_bytes(url, timeout=timeout).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallerError(f"invalid JSON returned by {url}") from exc
    if not isinstance(value, dict):
        raise InstallerError(f"unexpected release response from {url}")
    return value


def build_plan(
    release: dict[str, Any],
    destination_dir: Path,
    *,
    system: Optional[str] = None,
    architecture: Optional[str] = None,
) -> InstallPlan:
    tag = str(release.get("tag_name", ""))
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", tag):
        raise InstallerError("release response has an invalid tag_name")
    version = tag[1:]
    os_name = normalize_system(system)
    arch = normalize_architecture(architecture)
    extension = ".zip" if os_name == "windows" else ".tar.gz"
    archive_name = f"byteplus-cli_{version}_{os_name}_{arch}{extension}"
    checksum_name = f"byteplus-cli_{version}_SHA256SUMS"

    assets = release.get("assets")
    if not isinstance(assets, list):
        raise InstallerError("release response does not contain assets")
    by_name: dict[str, str] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        url = asset.get("browser_download_url")
        if isinstance(name, str) and isinstance(url, str):
            by_name[name] = url

    try:
        archive_url = by_name[archive_name]
        checksum_url = by_name[checksum_name]
    except KeyError as exc:
        raise InstallerError(
            f"official release does not contain {exc.args[0]}"
        ) from exc

    expected_asset_prefix = f"{RELEASE_DOWNLOAD_PREFIX}{tag}/"
    for url in (archive_url, checksum_url):
        if not url.startswith(expected_asset_prefix):
            raise InstallerError(f"refusing unexpected release asset URL: {url}")

    binary_name = "bp.exe" if os_name == "windows" else "bp"
    destination = destination_dir.expanduser().resolve() / binary_name
    return InstallPlan(
        version=version,
        tag=tag,
        system=os_name,
        architecture=arch,
        archive_name=archive_name,
        archive_url=archive_url,
        checksum_name=checksum_name,
        checksum_url=checksum_url,
        destination=str(destination),
    )


def parse_checksum(checksum_text: str, archive_name: str) -> str:
    for line in checksum_text.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        digest, filename = parts
        filename = filename.lstrip("*").strip()
        if filename == archive_name:
            if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                raise InstallerError(f"invalid checksum for {archive_name}")
            return digest.lower()
    raise InstallerError(f"checksum file has no entry for {archive_name}")


def normalize_sha256(value: str) -> str:
    digest = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise InstallerError("--sha256 must be exactly 64 hexadecimal characters")
    return digest


def _safe_member_name(name: str, binary_name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.name == binary_name
        and "__MACOSX" not in path.parts
    )


def extract_binary(archive_path: Path, system: str) -> bytes:
    try:
        return _extract_binary(archive_path, system)
    except InstallerError:
        raise
    except (OSError, tarfile.TarError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise InstallerError(f"invalid release archive: {exc}") from exc


def _extract_binary(archive_path: Path, system: str) -> bytes:
    binary_name = "bp.exe" if system == "windows" else "bp"
    candidate: Optional[bytes] = None

    if archive_path.name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise InstallerError("release archive contains too many members")
            if sum(max(info.file_size, 0) for info in members) > MAX_EXPANDED_BYTES:
                raise InstallerError("release archive expands beyond the safety limit")
            for info in members:
                if info.is_dir() or not _safe_member_name(info.filename, binary_name):
                    continue
                if candidate is not None:
                    raise InstallerError(
                        f"expected exactly one {binary_name} in release archive; found multiple"
                    )
                mode = info.external_attr >> 16
                if mode and stat.S_ISLNK(mode):
                    raise InstallerError(
                        "refusing a symlinked binary in release archive"
                    )
                if info.file_size > MAX_BINARY_BYTES:
                    raise InstallerError(
                        "binary in release archive is unexpectedly large"
                    )
                candidate = archive.read(info)
    else:
        with tarfile.open(archive_path, mode="r|gz") as archive:
            member_count = 0
            expanded_bytes = 0
            for member in archive:
                member_count += 1
                expanded_bytes += max(member.size, 0)
                if member_count > MAX_ARCHIVE_MEMBERS:
                    raise InstallerError("release archive contains too many members")
                if expanded_bytes > MAX_EXPANDED_BYTES:
                    raise InstallerError(
                        "release archive expands beyond the safety limit"
                    )
                if not member.isfile() or not _safe_member_name(
                    member.name, binary_name
                ):
                    continue
                if candidate is not None:
                    raise InstallerError(
                        f"expected exactly one {binary_name} in release archive; found multiple"
                    )
                if member.size > MAX_BINARY_BYTES:
                    raise InstallerError(
                        "binary in release archive is unexpectedly large"
                    )
                stream = archive.extractfile(member)
                if stream is None:
                    raise InstallerError("unable to read binary from release archive")
                candidate = stream.read(MAX_BINARY_BYTES + 1)

    if candidate is None:
        raise InstallerError(
            f"expected exactly one {binary_name} in release archive; found none"
        )
    if not candidate or len(candidate) > MAX_BINARY_BYTES:
        raise InstallerError("extracted binary has an invalid size")
    return candidate


def install(
    plan: InstallPlan,
    *,
    force: bool = False,
    timeout: float = 30,
    expected_sha256: Optional[str] = None,
) -> str:
    destination = Path(plan.destination)
    if destination.exists() and not force:
        raise InstallerError(
            f"destination already exists: {destination}; use --force only after review"
        )

    with tempfile.TemporaryDirectory(prefix="byteplus-cli-install-") as temporary:
        temp_dir = Path(temporary)
        checksum_bytes = fetch_bytes(
            plan.checksum_url, timeout=timeout, limit=1024 * 1024
        )
        archive_bytes = fetch_bytes(plan.archive_url, timeout=timeout)
        try:
            checksum_text = checksum_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InstallerError("release checksum file is not valid UTF-8") from exc
        expected = parse_checksum(checksum_text, plan.archive_name)
        actual = hashlib.sha256(archive_bytes).hexdigest()
        if actual != expected:
            raise InstallerError(
                f"SHA-256 mismatch for {plan.archive_name}: expected {expected}, got {actual}"
            )
        if expected_sha256 is not None:
            pinned = normalize_sha256(expected_sha256)
            if actual != pinned:
                raise InstallerError(
                    f"pinned SHA-256 mismatch for {plan.archive_name}: "
                    f"expected {pinned}, got {actual}"
                )

        archive_path = temp_dir / plan.archive_name
        archive_path.write_bytes(archive_bytes)
        candidate_bytes = extract_binary(archive_path, plan.system)
        candidate_path = temp_dir / ("bp.exe" if plan.system == "windows" else "bp")
        candidate_path.write_bytes(candidate_bytes)

        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, staging_name = tempfile.mkstemp(
            prefix=f".{destination.name}.install-", dir=destination.parent
        )
        os.close(descriptor)
        staging = Path(staging_name)
        try:
            shutil.copyfile(candidate_path, staging)
            if plan.system != "windows":
                staging.chmod(0o755)
            os.replace(staging, destination)
        finally:
            try:
                staging.unlink()
            except FileNotFoundError:
                pass
        return actual


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install an official BytePlus CLI GitHub release with SHA-256 verification."
    )
    parser.add_argument(
        "--version",
        default="latest",
        help="Exact release version; 'latest' is allowed only for --dry-run discovery.",
    )
    parser.add_argument(
        "--dest",
        default=str(Path.home() / ".local" / "bin"),
        help="Destination directory (default: ~/.local/bin).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve and print the official release plan without downloading or writing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing destination binary after verification.",
    )
    parser.add_argument(
        "--sha256",
        help=(
            "Independently obtained archive SHA-256 pin; the release checksum must also match."
        ),
    )
    parser.add_argument(
        "--trust-official-release",
        action="store_true",
        help=(
            "Explicitly accept the official GitHub release and its same-channel checksum "
            "without an independently obtained SHA-256 pin."
        ),
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON."
    )
    parser.add_argument(
        "--timeout", type=float, default=30, help="Network/process timeout."
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        pinned_sha256 = normalize_sha256(args.sha256) if args.sha256 else None
        if not args.dry_run and args.version == "latest":
            raise InstallerError(
                "installation requires an exact --version; use --dry-run to resolve and review latest"
            )
        if not args.dry_run and not pinned_sha256 and not args.trust_official_release:
            raise InstallerError(
                "installation requires --sha256 from an independent source or explicit "
                "--trust-official-release acceptance"
            )
        release = resolve_release(args.version, timeout=args.timeout)
        plan = build_plan(release, Path(args.dest))
        trust_mode = (
            "independent_digest"
            if pinned_sha256
            else "upstream_checksum_only"
            if args.trust_official_release
            else "plan_only"
        )
        payload: dict[str, Any] = {
            "plan": asdict(plan),
            "dry_run": args.dry_run,
            "trust_mode": trust_mode,
        }
        if pinned_sha256:
            payload["pinned_sha256"] = pinned_sha256
        if not args.dry_run:
            payload["installed_sha256"] = install(
                plan,
                force=args.force,
                timeout=args.timeout,
                expected_sha256=pinned_sha256,
            )
            payload["installed"] = True
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            if args.dry_run:
                print(f"Would install BytePlus CLI {plan.version}")
            else:
                print(f"Installed BytePlus CLI {plan.version}")
            print(f"Asset: {plan.archive_url}")
            print(f"Checksum: {plan.checksum_url}")
            print(f"Destination: {plan.destination}")
        return 0
    except InstallerError as exc:
        message = str(exc)
        if args.json:
            print(json.dumps({"error": message}, sort_keys=True))
        else:
            print(f"error: {message}", file=sys.stderr)
        return 1
    except (
        OSError,
        UnicodeError,
        ValueError,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as exc:
        message = f"installation failed safely: {exc}"
        if args.json:
            print(json.dumps({"error": message}, sort_keys=True))
        else:
            print(f"error: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
