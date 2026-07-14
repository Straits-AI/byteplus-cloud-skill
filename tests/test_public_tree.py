from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_public_tree.py"
SPEC = importlib.util.spec_from_file_location("check_public_tree", MODULE_PATH)
assert SPEC and SPEC.loader
public_tree = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(public_tree)


class PublicTreeTests(unittest.TestCase):
    def check_path_in(self, root: Path, relative: str) -> list[str]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
        with mock.patch.object(public_tree, "ROOT", root):
            return public_tree.check_path(path)

    def check_content_in(self, root: Path, relative: str, content: str) -> list[str]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        with mock.patch.object(public_tree, "ROOT", root):
            return public_tree.check_content(path)

    def test_rejects_sensitive_runtime_filenames(self) -> None:
        forbidden = (
            ".env.production",
            "production.tfvars",
            "byteplus.project.yaml",
            "client.pfx",
            "kubeconfig.prod",
            "deployment.log",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for filename in forbidden:
                with self.subTest(filename=filename):
                    self.assertTrue(self.check_path_in(root, filename))

    def test_allows_the_bundled_manifest_template(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self.check_path_in(
                root, "skills/byteplus-cloud/assets/byteplus.project.yaml"
            )
        self.assertEqual(errors, [])

    def test_rejects_non_utf8_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "opaque.bin"
            path.write_bytes(b"\xff\xfe")
            with mock.patch.object(public_tree, "ROOT", root):
                errors = public_tree.check_content(path)
        self.assertTrue(any("non-UTF-8" in error for error in errors))

    def test_rejects_private_acceptance_artifacts(self) -> None:
        fixtures = {
            "resource.md": "created " + "vpc-" + "abcdef123456",
            "request.md": "request " + "20260714" + "ABCDEF0123456789ABCDEF012345",
            "home.md": "stored at " + "/Users/" + "alice/private/project",
            "network.md": "endpoint " + "8." + "8.8.8",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for filename, content in fixtures.items():
                with self.subTest(filename=filename):
                    self.assertTrue(self.check_content_in(root, filename, content))

    def test_allows_placeholders_and_documentation_networks(self) -> None:
        content = (
            "Account: <account-id>\n"
            "Resource: <resource-id>\n"
            "Documentation hosts: 192.0.2.1, 198.51.100.2, 203.0.113.3\n"
            "Local service: 127.0.0.1\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            errors = self.check_content_in(root, "example.md", content)
        self.assertEqual(errors, [])

    @unittest.skipIf(os.name == "nt", "symlink behavior differs on Windows")
    def test_rejects_symlinks_that_escape_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(root_dir)
            target = Path(outside_dir) / "target.md"
            target.write_text("outside\n", encoding="utf-8")
            link = root / "link.md"
            link.symlink_to(target)
            with mock.patch.object(public_tree, "ROOT", root):
                errors = public_tree.check_path(link)
        self.assertTrue(any("symlink escapes" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
