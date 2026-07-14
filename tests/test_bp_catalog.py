from __future__ import annotations

import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "byteplus-cloud" / "scripts" / "bp_catalog.py"
SPEC = importlib.util.spec_from_file_location("bp_catalog", MODULE_PATH)
assert SPEC and SPEC.loader
catalog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = catalog
SPEC.loader.exec_module(catalog)


ROOT_HELP = """Usage:\n  bp [service] [action]\n\nAvailable Commands:\n  Service   Description\n  -------   -----------\n  ecs       Elastic Compute Service\n  login     Log in via browser\n  sts       Security Token Service\n\nFlags:\n  -h, --help\n"""

SERVICE_HELP = """Available Actions:\n  Action             Description\n  ------             -----------\n  DescribeInstances  List instances\n  RunInstances       Create instances\n\nUse \"bp ecs [action] --help\" for more information.\n\nFixed Flags:\n  ---profile string\n"""

ACTION_HELP = """Usage:\n  bp ecs RunInstances [params]\n\nAvailable Parameters:\n  --ClientToken  string\n  --Count        integer\n  --DryRun       boolean\n\nFixed Flags:\n  ---profile string  Profile\n  ---region string   Region\n"""


class CatalogTests(unittest.TestCase):
    def test_parses_services_actions_and_parameters(self) -> None:
        services = catalog.parse_entries(ROOT_HELP, "Available Commands:")
        self.assertEqual([item.name for item in services], ["ecs", "login", "sts"])
        actions = catalog.parse_entries(SERVICE_HELP, "Available Actions:")
        self.assertEqual(
            [item.name for item in actions], ["DescribeInstances", "RunInstances"]
        )
        parameters = catalog.parse_parameters(ACTION_HELP)
        self.assertEqual(
            [(item.name, item.type) for item in parameters],
            [("ClientToken", "string"), ("Count", "integer"), ("DryRun", "boolean")],
        )
        self.assertEqual(
            [item.name for item in catalog.parse_fixed_flags(ACTION_HELP)],
            ["---profile", "---region"],
        )
        self.assertEqual(
            catalog.parse_usage(ACTION_HELP), "bp ecs RunInstances [params]"
        )

    def test_parses_wide_table_entry_with_one_column_space(self) -> None:
        help_text = (
            "Available Commands:\n"
            "  Service            Description\n"
            "  -------            -----------\n"
            "  mlplatform20240701 BytePlus machine learning service.\n"
            "\nFlags:\n"
        )
        entries = catalog.parse_entries(help_text, "Available Commands:")
        self.assertEqual(entries[0].name, "mlplatform20240701")
        self.assertEqual(entries[0].description, "BytePlus machine learning service.")

    def test_rejects_non_identifier_arguments(self) -> None:
        with self.assertRaises(catalog.CatalogError):
            catalog.validate_identifier("ecs;rm", "service")

    @unittest.skipIf(os.name == "nt", "test uses POSIX executable permissions")
    def test_plain_bp_name_resolves_from_path_not_current_directory(self) -> None:
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            local = Path(temporary) / "bp"
            local.write_text("#!/bin/sh\n", encoding="utf-8")
            local.chmod(local.stat().st_mode | stat.S_IXUSR)
            try:
                os.chdir(temporary)
                with mock.patch.object(
                    catalog.shutil, "which", return_value="/trusted/path/bp"
                ):
                    self.assertEqual(catalog.resolve_bp("bp"), "/trusted/path/bp")
                self.assertEqual(catalog.resolve_bp("./bp"), str(local.resolve()))
            finally:
                os.chdir(original)

    def test_inspection_environment_drops_credentials(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "BYTEPLUS_ACCESS_KEY": "must-not-pass",
                "AWS_SECRET_ACCESS_KEY": "must-not-pass",
            },
            clear=False,
        ):
            env = catalog.inspection_env("/isolated/home")
        self.assertNotIn("BYTEPLUS_ACCESS_KEY", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertEqual(env["HOME"], "/isolated/home")

    @unittest.skipIf(os.name == "nt", "fixture uses a POSIX executable script")
    def test_cli_exports_json_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "bp"
            executable.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = version ]; then printf '%s\\n' 'BytePlus CLI version 9.9.9'; exit 0; fi\n"
                'if [ "$1" = ecs ] && [ "$2" = RunInstances ]; then cat <<\'EOF\'\n'
                + ACTION_HELP
                + "EOF\nexit 0\nfi\n"
                "if [ \"$1\" = ecs ]; then cat <<'EOF'\n"
                + SERVICE_HELP
                + "EOF\nexit 0\nfi\n"
                "cat <<'EOF'\n" + ROOT_HELP + "EOF\n",
                encoding="utf-8",
            )
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(catalog.main(["--bp", str(executable), "services"]), 0)
            exported = json.loads(output.getvalue())
            self.assertEqual(exported["version"], "BytePlus CLI version 9.9.9")
            self.assertEqual(exported["service_count"], 2)
            described = catalog.describe_action(
                str(executable), "ecs", "RunInstances", 2
            )
            serialized = json.dumps(described)
            self.assertIn("ClientToken", serialized)
            self.assertIn("required fields are not reliably marked", serialized)


if __name__ == "__main__":
    unittest.main()
