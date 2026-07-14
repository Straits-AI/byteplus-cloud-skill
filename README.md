# BytePlus Cloud Skill

[![CI](https://github.com/Straits-AI/byteplus-cloud-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/Straits-AI/byteplus-cloud-skill/actions/workflows/ci.yml)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-5b5bd6)](https://agentskills.io)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-public%20preview-orange.svg)](docs/validation-matrix.md)

An open [Agent Skill](https://agentskills.io) that helps coding agents plan,
provision, deploy, inspect, and troubleshoot applications on BytePlus Cloud.

> **Public preview:** this project is production-minded, but validation is
> capability-specific. It is not an official BytePlus project, a universal
> BytePlus MCP server, or a guarantee that every BytePlus console operation is
> programmable.

## What it provides

The skill gives Codex, Claude Code, Cursor, and other compatible coding agents a
retrieval-first operating layer over current BytePlus tools:

- official `bp` CLI installation, OAuth authentication, action discovery, and
  structured invocation;
- infrastructure routing between `bp`, BytePlus Cloud Control Terraform,
  product SDKs, `nest`, and product-specific MCPs;
- procedures for ECS/VPC, veFaaS, Cloud Sandbox, ModelArk, Seed Speech, Edge
  Functions, TOS, VKE, databases, observability, and AgentKit;
- explicit cost, IAM, networking, secret, approval, verification, rollback, and
  cleanup boundaries; and
- small standard-library helpers for CLI diagnosis, catalog extraction, safe CLI
  installation, and a bounded Seed Speech smoke test.

The skill does not replace BytePlus APIs. It teaches an agent how to retrieve the
current contract, choose the right official interface, perform the operation, and
prove the result without leaking credentials.

## Validation status

Validation performed on 13–14 July 2026 used `bp` 1.0.17 in
`ap-southeast-1`. Raw account-specific ledgers are intentionally not published.

| Capability | Public-preview status |
|---|---|
| `bp` install, discovery, OAuth profile, and signed reads | Live validated |
| ECS provision, restricted SSH, app deployment, verification, and cleanup | Live end-to-end validated |
| veFaaS event function, release, timer invocation, and cleanup | Live end-to-end validated on the private event path |
| veFaaS Cloud Sandbox, private WebShell execution, and cleanup | Live end-to-end validated |
| ModelArk Seed text, Seedream image, and Seedance 1.5 video | Live bounded calls validated and cleaned up |
| Seed Speech TTS 2.0 | Live bounded call validated and restored inactive |
| AgentKit runtime and All-in-one sandbox creation | Read/auth validated; create path blocked by account entitlement |
| Public HTTP/APIG deployment | Not yet end-to-end validated |
| Seedance 2.0 | Not tested; its prepaid path was outside the test boundary |
| Edge Functions, TOS, VKE, managed databases, Terraform, and broad observability | Retrieval and runbook coverage; not part of the live acceptance suite |

See the [validation matrix](docs/validation-matrix.md) for proof criteria,
limitations, and the road to a stable 1.0 release.

## Install

### With the Skills CLI

Install globally and let the CLI select a supported coding agent:

```bash
npx skills add Straits-AI/byteplus-cloud-skill \
  --skill byteplus-cloud \
  --global
```

For a non-interactive Codex installation:

```bash
npx skills add Straits-AI/byteplus-cloud-skill \
  --skill byteplus-cloud \
  --agent codex \
  --global \
  --yes
```

The Skills CLI is a third-party distribution tool. Review its current behavior
before running it in a sensitive environment.

### Clone and copy

```bash
git clone https://github.com/Straits-AI/byteplus-cloud-skill.git
cd byteplus-cloud-skill
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/byteplus-cloud "${CODEX_HOME:-$HOME/.codex}/skills/"
```

For another compatible agent, copy `skills/byteplus-cloud` into that agent's
documented skill directory.

## Prerequisites

- Python 3.10 or newer for the bundled helpers.
- A BytePlus account for account inspection or deployment.
- A supported local coding agent with shell and file access.
- The official BytePlus CLI for control-plane operations.

If `bp` is absent, the skill first produces an official-release installation plan.
Actual installation requires an exact version and either an independent SHA-256
pin or explicit acceptance of the official release/checksum trust channel. It
installs into `$HOME/.local/bin/bp` only after the developer has already authorized
installation or explicitly approves that path. Authentication remains the
developer's action:

```bash
bp login --profile dev --region ap-southeast-1
```

The browser is used for OAuth and, where BytePlus exposes no current API, a
minimal account-owner activation or terms prerequisite. Deployment and resource
operations stay on the CLI or documented APIs.

## Use

Ask the coding agent naturally. Examples:

```text
Use the BytePlus skill to inspect this app and propose the smallest private
development deployment. Do not create resources until I approve the plan.
```

```text
Deploy this service to one disposable BytePlus ECS instance, restrict access to
my current /32, verify the health endpoint, and remove every run-owned resource.
```

```text
Use ModelArk for this image workflow. Retrieve current model IDs and pricing,
show the bounded test plan, keep keys out of logs, and delete the task record.
```

The agent should establish the exact profile, masked account, region,
environment, cost class, and cleanup owner before consequential changes.

## Documentation strategy

This repository does **not** mirror the BytePlus documentation corpus. Product
IDs, schemas, regions, prices, limits, availability, and release behavior change
too quickly for a bundled copy to remain authoritative.

The skill stores concise operational procedures and routes to official sources.
At execution time it retrieves current BytePlus documentation, CLI help, provider
schemas, SDK types, and release notes before relying on volatile details. Tested
experience is retained as guardrails, not as a frozen API catalog.

## Safety model

Coding agents can create billable resources and make destructive changes. The
skill requires:

- an explicit target profile, account, region, and environment;
- read-before-write inventory and stable ownership tags or exact IDs;
- current schemas and cost/security effects before mutation;
- additional review for production, public exposure, IAM/networking, prepaid or
  unbounded cost, replacement, and deletion;
- fresh control-plane, data-plane, and operations verification; and
- dependency-ordered cleanup with fresh absence checks.

Never paste BytePlus access keys, session tokens, ModelArk keys, Seed Speech keys,
signed URLs, or local profile files into an issue, pull request, prompt, or log.

## Repository layout

```text
skills/byteplus-cloud/   Portable skill, references, assets, helpers, and evals
tests/                   Offline unit and structural tests
docs/                    Sanitized validation and release boundaries
.github/                 CI, issue forms, and contribution templates
```

Private live-test ledgers and credentials are never part of the public tree.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q skills/byteplus-cloud/scripts
python3 scripts/check_public_tree.py
```

The tests are offline and must not require BytePlus credentials or mutate cloud
state. Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a capability or
live-validation change.

## Contributing and support

Issues and pull requests are welcome. Start with:

- [Contributing guide](CONTRIBUTING.md)
- [Support policy](SUPPORT.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)

## License and trademarks

Licensed under the [Apache License 2.0](LICENSE).

BytePlus and related product names are trademarks of their respective owners.
This community project is independently maintained by Straits AI and is not
endorsed by or affiliated with BytePlus.
