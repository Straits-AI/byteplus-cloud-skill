from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "byteplus-cloud"


class SkillStructureTests(unittest.TestCase):
    def test_skill_has_no_placeholders_and_stays_compact(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("TODO", text)
        self.assertLess(len(text.splitlines()), 500)

    def test_frontmatter_has_only_supported_keys(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        assert match
        keys = []
        for line in match.group(1).splitlines():
            if line and not line.startswith((" ", "\t")) and ":" in line:
                keys.append(line.split(":", 1)[0])
        self.assertEqual(keys, ["name", "description"])

    def test_all_relative_markdown_links_exist(self) -> None:
        for markdown in SKILL.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#", "<")):
                    continue
                target_path = target.split("#", 1)[0]
                self.assertTrue(
                    (markdown.parent / target_path).exists(),
                    f"broken link in {markdown}: {target}",
                )

    def test_every_reference_is_routed_from_skill(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        linked_references = {
            target.split("#", 1)[0]
            for target in re.findall(r"\[[^\]]+\]\((references/[^)]+)\)", skill_text)
        }
        actual_references = {
            path.relative_to(SKILL).as_posix()
            for path in (SKILL / "references").glob("*.md")
        }
        self.assertEqual(linked_references, actual_references)

    def test_mcp_asset_is_valid_json(self) -> None:
        path = SKILL / "assets" / "mcp.edge-functions.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        args = value["mcpServers"]["byteplus-edge-function"]["args"]
        self.assertEqual(args[1], "@byteplus/nest@1.3.2")
        self.assertEqual(args[-2:], ["mcp", "server"])

    def test_forward_evals_are_well_formed(self) -> None:
        value = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual(value["skill_name"], "byteplus-cloud")
        self.assertGreaterEqual(len(value["evals"]), 3)
        ids = [item["id"] for item in value["evals"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in value["evals"]:
            self.assertTrue(item["prompt"].strip())
            self.assertTrue(item["expected_output"].strip())
            self.assertGreaterEqual(len(item["expectations"]), 3)

    def test_openai_metadata_mentions_skill(self) -> None:
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$byteplus-cloud", text)
        self.assertIn("BytePlus Cloud", text)

    def test_missing_bp_requires_persistent_install_or_visible_prompt(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cli = (SKILL / "references" / "cli.md").read_text(encoding="utf-8")
        combined = skill + "\n" + cli
        self.assertIn("command -v bp", combined)
        self.assertIn("$HOME/.local/bin/bp", skill)
        self.assertIn("ask whether", skill)
        self.assertIn("already authorized", skill)
        self.assertIn("never reuse or report it", skill)
        self.assertIn("Do not merely continue with a temporary test binary", cli)

    def test_root_oauth_is_privileged_context_not_a_console_blocker(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cli = (SKILL / "references" / "cli.md").read_text(encoding="utf-8")
        security = (SKILL / "references" / "security.md").read_text(encoding="utf-8")
        combined = "\n".join((skill, cli, security))

        self.assertIn("accepted local-developer fast path", skill)
        self.assertIn("Never send the\n   developer to the console", skill)
        self.assertIn("Quick local (default)", skill)
        self.assertIn("Hardened local (optional)", skill)
        self.assertIn("Managed team (optional)", skill)
        self.assertIn("lead with\nthe answer", skill)
        self.assertIn("both IAM actions and STS `AssumeRole` are programmatic", skill)
        self.assertIn("production, public exposure, IAM/networking", skill)
        self.assertIn("requires explicit approval of the IAM changes", skill)
        self.assertIn("may require one-time administration", skill)
        self.assertIn("valid but privileged", cli)
        self.assertIn("Continue requested read-only operations immediately", security)
        self.assertRegex(security, r"do not force\s+IAM-console setup")
        self.assertIn("do not add another confirmation", security)
        self.assertIn("Optional hardening without routine console work", cli)
        self.assertIn("do not claim that automatic root-OAuth-to-role switching is complete", cli)
        self.assertNotIn("| Account critical | Root access", combined)

    def test_ecs_ssh_runbook_preserves_ownership_and_cleanup_order(self) -> None:
        ecs = (SKILL / "references" / "ecs-vpc.md").read_text(encoding="utf-8")

        self.assertIn("Run the bounded ECS-over-SSH workflow", ecs)
        self.assertIn("DryRunOperation", ecs)
        self.assertIn("dedicated `known_hosts`", ecs)
        self.assertIn("Do not disable host-key checking", ecs)
        self.assertIn("Record the implicit\n   primary ENI and system-volume IDs", ecs)
        self.assertIn("only the exact IDs in the run ledger", ecs)
        self.assertIn("Release the EIP", ecs)
        self.assertIn("Re-read reused VPC/subnet resources", ecs)
        self.assertIn("Report cleanup as `CLEAN` only", ecs)
        self.assertIn("ap-southeast-1", ecs)

    def test_vefaas_function_and_sandbox_runbooks_preserve_proof_boundaries(self) -> None:
        functions = (SKILL / "references" / "vefaas-functions.md").read_text(
            encoding="utf-8"
        )
        sandbox = (SKILL / "references" / "cloud-sandbox.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Verify all three layers", functions)
        self.assertIn("A timer-trigger smoke test proves event execution", functions)
        self.assertIn("public HTTP remains unverified", functions)
        self.assertIn("Report cleanup as `CLEAN` only", functions)
        self.assertIn("FunctionType: sandbox", sandbox)
        self.assertIn("tested-but-live-revalidate", sandbox)
        self.assertIn("`FunctionType` and `Port`", sandbox)
        self.assertIn("InvalidActionOrVersion", sandbox)
        self.assertIn("GenWebshellEndpoint", sandbox)
        self.assertIn("ticket", sandbox)
        self.assertIn("Do not treat `Terminating` as final absence", sandbox)
        self.assertIn("Report `CLEAN` only", sandbox)
        self.assertIn("private sandbox does not create a public URL", sandbox)
        self.assertIn("WebShell execution is not public HTTP", sandbox)

    def test_function_and_sandbox_forward_evals_cover_live_gaps(self) -> None:
        value = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in value["evals"]}

        self.assertIn(7, by_id)
        self.assertIn(8, by_id)
        self.assertIn("timer-triggered invocation", by_id[7]["prompt"])
        self.assertIn("RunCode", by_id[8]["prompt"])
        self.assertIn("public HTTP", " ".join(by_id[7]["expectations"]))
        self.assertIn("FunctionType", " ".join(by_id[8]["expectations"]))
        self.assertIn("CLEAN", " ".join(by_id[8]["expectations"]))

    def test_modelark_smoke_workflow_is_secret_safe_and_bounded(self) -> None:
        modelark = (SKILL / "references" / "modelark.md").read_text(encoding="utf-8")

        self.assertIn("ModelNotOpen", modelark)
        self.assertIn("NotFound.Presetendpoint", modelark)
        self.assertIn("argument array", modelark)
        self.assertIn("fake `bp` and HTTP fixtures", modelark)
        self.assertIn("do not exceed 32", modelark)
        self.assertIn("smallest currently supported resolution", modelark)
        self.assertIn("Poll with bounded backoff and a deadline", modelark)
        self.assertIn("unconditional `finally` path", modelark)
        self.assertIn("Success is not cleanup", modelark)
        self.assertIn("normally `404` or `410`", modelark)
        self.assertIn("long-term application key", modelark)
        self.assertNotIn("seed-2-0-lite-", modelark)
        self.assertNotIn("seedream-5-0-", modelark)
        self.assertNotIn("seedance-2-0-", modelark)

    def test_agentkit_runbook_preserves_oauth_activation_and_proof_boundaries(self) -> None:
        agentkit = (SKILL / "references" / "agentkit.md").read_text(encoding="utf-8")
        value = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in value["evals"]}

        self.assertIn("`clicreds.CliProvider`", agentkit)
        self.assertIn("InvalidActionOrVersion", agentkit)
        self.assertIn("account-owner decisions", agentkit)
        self.assertIn("Do not assume the AgentKit CLI natively", agentkit)
        self.assertIn("AgentKit managed tools and veFaaS Cloud Sandbox are distinct", agentkit)
        self.assertIn("agentkit-sdk-python==0.7.13", agentkit)
        self.assertIn("a2a-sdk==0.3.7", agentkit)
        self.assertIn("/.well-known/agent-card.json", agentkit)
        self.assertIn("`message/send`", agentkit)
        self.assertIn("generated API key in plaintext", agentkit)
        self.assertIn("Do not equate Container Registry", agentkit)
        self.assertIn("blind retry can fail with a duplicate", agentkit)
        self.assertIn("`Error` at version 0", agentkit)
        self.assertIn("minimum replica of 1", agentkit)
        self.assertIn("Report `CLEAN` only", agentkit)
        self.assertIn(9, by_id)
        self.assertIn("ListRuntimes", by_id[9]["prompt"])
        self.assertIn("credential-isolating", " ".join(by_id[9]["expectations"]))

    def test_managed_service_readiness_covers_issue_three_failures(self) -> None:
        readiness = (SKILL / "references" / "service-readiness.md").read_text(
            encoding="utf-8"
        )
        cli = (SKILL / "references" / "cli.md").read_text(encoding="utf-8")
        security = (SKILL / "references" / "security.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("An `InternalError` is a symptom, not a diagnosis", readiness)
        self.assertIn("ServiceRoleForKafka", readiness)
        self.assertIn("CreateServiceLinkedRole", readiness)
        self.assertIn("KMS_ServiceNotOpen", readiness)
        self.assertIn("`DescribeInstances` is paginated", readiness)
        self.assertIn("`CreateInstance` takes `ZoneId`", readiness)
        self.assertIn("Do not use dotted flattened flags", readiness)
        self.assertIn("DeletePublicAddress", readiness)
        self.assertIn("release only the run-owned EIP", readiness)
        self.assertIn("JavaScript applications", cli)
        self.assertIn("protected stdin/file", cli)
        self.assertIn("Do not\ngrant `IAMFullAccess`", security)

        value = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in value["evals"]}
        self.assertIn(22, by_id)
        self.assertIn("InternalError 500", by_id[22]["prompt"])
        self.assertIn("ServiceRoleForKafka", " ".join(by_id[22]["expectations"]))

    def test_seed_speech_has_a_separate_activation_and_secret_boundary(self) -> None:
        speech = (SKILL / "references" / "seed-speech.md").read_text(encoding="utf-8")

        self.assertIn("not a ModelArk model", speech)
        self.assertIn("App ID", speech)
        self.assertIn("current access credential", speech)
        self.assertIn("resource ID", speech)
        self.assertIn("UI-only prerequisites", speech)
        self.assertIn("never accept terms", speech)
        self.assertIn("mode-protected temporary file", speech)
        self.assertIn("non-zero duration", speech)

    def test_model_and_voice_forward_evals_cover_the_boundaries(self) -> None:
        value = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in value["evals"]}

        self.assertIn(20, by_id)
        self.assertIn(21, by_id)
        self.assertIn("ModelNotOpen", by_id[20]["prompt"])
        self.assertIn("ARK_API_KEY", by_id[21]["prompt"])
        self.assertIn("UI-only", " ".join(by_id[20]["expectations"]))
        self.assertIn("separate from ModelArk", " ".join(by_id[21]["expectations"]))

    def test_bundle_contains_expected_components(self) -> None:
        expected = [
            "SKILL.md",
            "agents/openai.yaml",
            "evals/evals.json",
            "scripts/install_bp.py",
            "scripts/byteplus_doctor.py",
            "scripts/bp_catalog.py",
            "references/sources.md",
            "references/cli.md",
            "references/iac.md",
            "references/edge-functions.md",
            "references/vefaas-functions.md",
            "references/cloud-sandbox.md",
            "references/modelark.md",
            "references/seed-speech.md",
            "references/agentkit.md",
            "references/databases.md",
            "references/service-readiness.md",
            "references/services.md",
            "references/operations.md",
            "references/security.md",
            "assets/byteplus.project.yaml",
            "assets/mcp.edge-functions.json",
        ]
        for relative in expected:
            self.assertTrue((SKILL / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
