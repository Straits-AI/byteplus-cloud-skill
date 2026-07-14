from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "byteplus-cloud" / "scripts" / "install_bp.py"
SPEC = importlib.util.spec_from_file_location("install_bp", MODULE_PATH)
assert SPEC and SPEC.loader
install_bp = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = install_bp
SPEC.loader.exec_module(install_bp)


class InstallBpTests(unittest.TestCase):
    def test_normalizes_supported_platforms(self) -> None:
        self.assertEqual(install_bp.normalize_system("Darwin"), "darwin")
        self.assertEqual(install_bp.normalize_system("win32"), "windows")
        self.assertEqual(install_bp.normalize_architecture("x86_64"), "amd64")
        self.assertEqual(install_bp.normalize_architecture("aarch64"), "arm64")

    def test_build_plan_accepts_only_official_release_assets(self) -> None:
        base = "https://github.com/byteplus-sdk/byteplus-cli/releases/download/v1.2.3/"
        release = {
            "tag_name": "v1.2.3",
            "assets": [
                {
                    "name": "byteplus-cli_1.2.3_linux_amd64.tar.gz",
                    "browser_download_url": base
                    + "byteplus-cli_1.2.3_linux_amd64.tar.gz",
                },
                {
                    "name": "byteplus-cli_1.2.3_SHA256SUMS",
                    "browser_download_url": base + "byteplus-cli_1.2.3_SHA256SUMS",
                },
            ],
        }
        plan = install_bp.build_plan(
            release, Path("/tmp/bin"), system="linux", architecture="amd64"
        )
        self.assertEqual(plan.version, "1.2.3")
        self.assertEqual(plan.archive_name, "byteplus-cli_1.2.3_linux_amd64.tar.gz")
        self.assertTrue(plan.destination.endswith("/tmp/bin/bp"))

        release["assets"][0]["browser_download_url"] = "https://example.com/bp.tar.gz"
        with self.assertRaises(install_bp.InstallerError):
            install_bp.build_plan(
                release, Path("/tmp/bin"), system="linux", architecture="amd64"
            )

        release["assets"][0]["browser_download_url"] = (
            "https://github.com/byteplus-sdk/byteplus-cli/releases/download/v9.9.9/"
            "byteplus-cli_1.2.3_linux_amd64.tar.gz"
        )
        with self.assertRaises(install_bp.InstallerError):
            install_bp.build_plan(
                release, Path("/tmp/bin"), system="linux", architecture="amd64"
            )

    def test_parses_exact_checksum_entry(self) -> None:
        digest = hashlib.sha256(b"archive").hexdigest()
        text = f"{'0' * 64}  other.tar.gz\n{digest} *wanted.tar.gz\n"
        self.assertEqual(install_bp.parse_checksum(text, "wanted.tar.gz"), digest)
        with self.assertRaises(install_bp.InstallerError):
            install_bp.parse_checksum(text, "missing.tar.gz")

    def test_validates_optional_pinned_digest(self) -> None:
        digest = "a" * 64
        self.assertEqual(install_bp.normalize_sha256(digest.upper()), digest)
        with self.assertRaises(install_bp.InstallerError):
            install_bp.normalize_sha256("not-a-digest")

    def test_extracts_one_regular_binary_from_tar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "release.tar.gz"
            data = b"fake-byteplus-binary"
            with tarfile.open(archive_path, "w:gz") as archive:
                info = tarfile.TarInfo("release/bp")
                info.size = len(data)
                info.mode = 0o755
                archive.addfile(info, io.BytesIO(data))
            self.assertEqual(install_bp.extract_binary(archive_path, "linux"), data)

    def test_extracts_one_regular_binary_from_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "release.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("release/bp.exe", b"fake-windows-binary")
            self.assertEqual(
                install_bp.extract_binary(archive_path, "windows"),
                b"fake-windows-binary",
            )

    def test_rejects_ambiguous_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "release.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                for name in ("one/bp", "two/bp"):
                    data = name.encode()
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
            with self.assertRaises(install_bp.InstallerError):
                install_bp.extract_binary(archive_path, "linux")

    def test_rejects_corrupt_archive_with_installer_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "release.tar.gz"
            archive_path.write_bytes(b"not-a-tarball")
            with self.assertRaises(install_bp.InstallerError):
                install_bp.extract_binary(archive_path, "linux")

    def test_plan_is_json_serializable(self) -> None:
        base = "https://github.com/byteplus-sdk/byteplus-cli/releases/download/v1.2.3/"
        release = {
            "tag_name": "v1.2.3",
            "assets": [
                {
                    "name": "byteplus-cli_1.2.3_darwin_arm64.tar.gz",
                    "browser_download_url": base
                    + "byteplus-cli_1.2.3_darwin_arm64.tar.gz",
                },
                {
                    "name": "byteplus-cli_1.2.3_SHA256SUMS",
                    "browser_download_url": base + "byteplus-cli_1.2.3_SHA256SUMS",
                },
            ],
        }
        plan = install_bp.build_plan(
            release, Path("/tmp/bin"), system="darwin", architecture="arm64"
        )
        json.dumps(plan.__dict__)

    def test_explicit_version_builds_official_urls_without_api_metadata(self) -> None:
        release = install_bp.resolve_release("1.0.17")
        plan = install_bp.build_plan(release, Path("/tmp/bin"))
        self.assertEqual(plan.tag, "v1.0.17")
        self.assertTrue(plan.archive_url.startswith(install_bp.RELEASE_DOWNLOAD_PREFIX))

    def test_latest_release_falls_back_when_github_api_is_rate_limited(self) -> None:
        with (
            mock.patch.object(
                install_bp,
                "fetch_json",
                side_effect=install_bp.InstallerError("HTTP 403"),
            ),
            mock.patch.object(
                install_bp,
                "resolve_latest_tag",
                return_value="v1.0.17",
            ),
        ):
            release = install_bp.resolve_release("latest")
        self.assertEqual(release["tag_name"], "v1.0.17")

    def test_install_verifies_bytes_without_executing_candidate(self) -> None:
        archive_bytes = b"fixture-archive"
        digest = hashlib.sha256(archive_bytes).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "bin" / "bp"
            plan = install_bp.InstallPlan(
                version="1.2.3",
                tag="v1.2.3",
                system="linux",
                architecture="amd64",
                archive_name="byteplus-cli_1.2.3_linux_amd64.tar.gz",
                archive_url="https://example.invalid/archive",
                checksum_name="byteplus-cli_1.2.3_SHA256SUMS",
                checksum_url="https://example.invalid/checksum",
                destination=str(destination),
            )
            checksum = f"{digest}  {plan.archive_name}\n".encode()
            with (
                mock.patch.object(
                    install_bp, "fetch_bytes", side_effect=[checksum, archive_bytes]
                ),
                mock.patch.object(
                    install_bp, "extract_binary", return_value=b"not-executable"
                ),
            ):
                installed_digest = install_bp.install(
                    plan, expected_sha256=digest.upper()
                )
            self.assertEqual(installed_digest, digest)
            self.assertEqual(destination.read_bytes(), b"not-executable")

    def test_json_mode_normalizes_expected_runtime_failures(self) -> None:
        stdout = io.StringIO()
        with mock.patch.object(
            install_bp, "resolve_release", side_effect=OSError("filesystem failure")
        ):
            with redirect_stdout(stdout):
                code = install_bp.main(["--version", "1.0.17", "--dry-run", "--json"])
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertIn("filesystem failure", payload["error"])

    def test_install_requires_exact_version_before_resolution(self) -> None:
        stdout = io.StringIO()
        with (
            mock.patch.object(install_bp, "resolve_release") as resolve,
            redirect_stdout(stdout),
        ):
            code = install_bp.main(["--json", "--trust-official-release"])
        self.assertEqual(code, 1)
        self.assertIn("exact --version", json.loads(stdout.getvalue())["error"])
        resolve.assert_not_called()

    def test_install_requires_independent_pin_or_explicit_upstream_trust(self) -> None:
        stdout = io.StringIO()
        with (
            mock.patch.object(install_bp, "resolve_release") as resolve,
            redirect_stdout(stdout),
        ):
            code = install_bp.main(["--version", "1.0.17", "--json"])
        self.assertEqual(code, 1)
        self.assertIn("--sha256", json.loads(stdout.getvalue())["error"])
        resolve.assert_not_called()

    def test_exact_install_records_explicit_upstream_trust_mode(self) -> None:
        release = {"tag_name": "v1.0.17", "assets": []}
        plan = install_bp.InstallPlan(
            version="1.0.17",
            tag="v1.0.17",
            system="linux",
            architecture="amd64",
            archive_name="byteplus-cli_1.0.17_linux_amd64.tar.gz",
            archive_url="https://example.invalid/archive",
            checksum_name="byteplus-cli_1.0.17_SHA256SUMS",
            checksum_url="https://example.invalid/checksum",
            destination="/isolated/bin/bp",
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(install_bp, "resolve_release", return_value=release),
            mock.patch.object(install_bp, "build_plan", return_value=plan),
            mock.patch.object(install_bp, "install", return_value="a" * 64),
            redirect_stdout(stdout),
        ):
            code = install_bp.main(
                [
                    "--version",
                    "1.0.17",
                    "--trust-official-release",
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["trust_mode"], "upstream_checksum_only")
        self.assertTrue(payload["installed"])

    def test_dry_run_may_resolve_latest_without_trust_acceptance(self) -> None:
        release = {"tag_name": "v1.0.17", "assets": []}
        plan = install_bp.InstallPlan(
            version="1.0.17",
            tag="v1.0.17",
            system="linux",
            architecture="amd64",
            archive_name="byteplus-cli_1.0.17_linux_amd64.tar.gz",
            archive_url="https://example.invalid/archive",
            checksum_name="byteplus-cli_1.0.17_SHA256SUMS",
            checksum_url="https://example.invalid/checksum",
            destination="/isolated/bin/bp",
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(install_bp, "resolve_release", return_value=release),
            mock.patch.object(install_bp, "build_plan", return_value=plan),
            redirect_stdout(stdout),
        ):
            code = install_bp.main(["--dry-run", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["trust_mode"], "plan_only")


if __name__ == "__main__":
    unittest.main()
