# AgentKit application workflow

Use AgentKit only when the application itself is an agent runtime, managed tool,
memory, knowledge base, skill, or MCP integration. Do not route an ordinary web
service to AgentKit.

## Separate the lifecycle and prerequisites

Treat a custom AgentKit runtime deployment as a dependency graph:

```text
account entitlement / beta agreement
-> explicit profile, identity, region, and project
-> AgentKit service role and least-privilege policies
-> Container Registry artifact or supported package source
-> optional ModelArk endpoint/key and other dependent services
-> runtime or managed tool
-> release / session / invocation
-> logs, metrics, and exact cleanup
```

Current prerequisites and billing can change while the product is in preview.
Retrieve them before every deployment. Activation, a customer agreement, billing
setup, and service-role consent are account-owner decisions. If the current
public API has no activation action, state the one UI step and stop; never accept
terms, activate paid use, or create IAM silently.

Activation is not self-service for every account. A July 2026 developer account
was redirected from the AgentKit console to a `Talk to an expert` beta-product
page with no activation control. Treat that as an entitlement blocker. Do not
submit a sales/contact request, message an external party, or create IAM, CR, TOS,
or ModelArk dependencies without the user's separate authorization; those actions
cannot bypass the missing entitlement.

## Discover the live contract

Inspect the installed CLI and official OpenAPI rather than relying on the command
examples in this reference:

```bash
agentkit --version
agentkit --help
agentkit runtime --help
agentkit tools --help
agentkit tools session --help
```

Retrieve the current service address, API version, regional availability, runtime
and tool schemas, supported artifact types, specifications, timeouts, prices, and
dependency requirements. The current AgentKit lifecycle includes commands such as
`init`, `config`, `build`, `deploy`/`launch`, `status`, `invoke`, and `destroy`,
plus lower-level runtime and tool management; treat installed help as the command
contract.

Before mutation, inventory runtimes, tools, sessions, service roles, Container
Registry artifacts, and related ModelArk resources. Open a sanitized run ledger
with the exact profile/account/region/project, deterministic run prefix, created
IDs, request IDs, dependency ownership, cost/lifetime, and cleanup actions.

## Reuse `bp login` without exposing credentials

Do not assume the AgentKit CLI natively reads a `bp login` profile. The tested
AgentKit CLI baseline documented AK/SK configuration, while the official BytePlus
Go SDK exposes `clicreds.CliProvider` for resolving an existing named BytePlus CLI
profile.

A live July 2026 test proved that `clicreds.CliProvider` could use a console-login
OAuth profile to sign AgentKit OpenAPI requests. It also proved that an isolated
parent process could resolve temporary credentials in memory and provide them
only to an AgentKit CLI child process. No AK/SK was printed or persisted.

Apply this boundary when OAuth reuse is required:

1. Pin and inspect the current official BytePlus SDK and AgentKit CLI versions.
2. Resolve the explicit named profile in a small local process using the SDK
   provider; never parse or print `~/.byteplus/config.json`.
3. Launch the exact AgentKit child command with an argument array and temporary
   credentials only in that child's environment.
4. Disable shell tracing and debug dumps. Never print the child environment,
   credentials, authorization headers, or raw configuration.
5. Remove the credentials when the child exits and rely on the provider's normal
   refresh behavior for a later invocation.

This is a tested interoperability pattern, not proof that all future AgentKit CLI
versions support OAuth. Prefer native profile support if current official help
adds it. Do not copy OAuth-derived credentials into global AgentKit configuration,
source files, manifests, process arguments, or the agent transcript.

## Diagnose activation before creating dependencies

Run authenticated, read-only `ListRuntimes` and `ListTools` calls first. A
successful list proves identity, signing, endpoint, region, and read authorization;
it does not prove create entitlement.

If documented create actions such as `CreateRuntime`, `CreateTool`, or
`CreateSession` return `InvalidActionOrVersion` while list actions for the same
documented API version succeed:

1. Recheck the current action name, version, regional endpoint, and official
   release notes once.
2. Retry through one independent official surface, such as the current AgentKit
   CLI versus the official SDK, without guessing private versions or endpoints.
3. Check current activation and beta-agreement prerequisites.
4. If both official paths reject action dispatch and the account is not activated,
   classify activation as the blocker. Do not create IAM, CR, ModelArk, or TOS
   dependencies in an attempt to bypass it.
5. Preserve sanitized request IDs and run fresh list calls to prove that the failed
   probes created no resource.

The July 2026 developer-account test reached exactly this state: OAuth-signed
`ListRuntimes` and `ListTools` succeeded, while documented create actions returned
`InvalidActionOrVersion`; final inventories remained zero. This is evidence for
the prerequisite runbook, not a successful AgentKit deployment claim.

## Deploy an agent runtime

Only continue after service activation and the exact IAM/networking/cost plan are
approved.

1. Inspect the application, framework/protocol, entry point, dependency file,
   health behavior, model/tool access, secrets, outbound network, and observability
   needs.
2. Create or reuse the least-privilege AgentKit service role. Creating or attaching
   IAM policies is a separate security-sensitive mutation; record and later delete
   only a role owned by this run.
3. Select the current supported artifact path. For CLI-built cloud runtimes, verify
   Container Registry activation, repository ownership, image contents, and cleanup.
4. For a model-backed agent, verify ModelArk activation, exact endpoint/model,
   protected runtime key reference, region, quota, and cost. Read
   [modelark.md](modelark.md); do not place an API key in `agentkit.yaml` output or
   the transcript.
5. Build and test locally, scan the artifact, then create/launch one smallest
   bounded runtime with explicit project, role, CPU/memory, scale, environment,
   authentication, logging, and tags.
6. Record the runtime and artifact IDs immediately. Poll status with bounded
   backoff until the documented ready/error state.
7. Release the exact version, invoke one benign smoke request, and verify the
   expected application marker or response without logging model content or
   secrets.

Do not treat runtime creation as deployment success. Verify control plane, data
plane, and operations independently.

## Deploy an AgentKit sandbox tool

AgentKit managed tools and veFaaS Cloud Sandbox are distinct products. For an
AgentKit All-in-one or Skills Sandbox workflow:

An All-in-one (AIO) Sandbox is the smallest documented AgentKit proof after
entitlement. It does not require a customer Container Registry image, ModelArk
endpoint, TOS mount, or runtime service role. Public egress remains an explicit
network boundary. The lowest cross-document-safe proof is one run-tagged AIO tool
at 2,000 millicores and 4,096 MiB, no TOS, no private network, a generated API key
kept out of output, one 60-second session, and one benign `RunCode` marker.

1. Retrieve the current `CreateTool`, `CreateSession`, invocation, and delete
   schemas and supported tool types.
2. Confirm required service roles and policies. Current Skills Sandbox guidance
   may require TOS access; do not grant it to an unrelated tool.
3. Select the smallest current CPU/memory, shortest session TTL, no storage/VPC,
   and no public ingress unless explicitly required.
4. Create the tool, record its ID, poll ready, create one short session, and run a
   benign marker workload.
5. Verify tool configuration, session result, logs/status, and a bounded failure
   case.
6. Delete the session, tool, and run-owned IAM/storage dependencies, then require
   fresh zero-result inventories.

If create actions are unavailable because AgentKit is not activated, do not claim
that the independent veFaaS sandbox test proves AgentKit AIO/Skills Sandbox.

## Verify and clean up

Verify at three levels:

- **Control plane:** exact runtime/tool/version/session state, role, artifact,
  region, project, scale, network, and authentication configuration.
- **Data plane:** one real invoke/session request with exact expected marker and a
  bounded negative case.
- **Operations:** bounded sanitized logs, status/metrics, deployment history, and
  rollback availability.

For an approved disposable run, stop traffic, delete sessions and releases as
required, delete the exact runtime/tool IDs, remove only run-owned CR artifacts and
IAM roles, and then query every created type by ID and stable name/tag. Preserve
shared roles, registries, models, keys, and logging projects. Report `CLEAN` only
after all run-owned cloud resources and local secret-bearing bridge state are
absent.

## Current official sources

- [What is AgentKit](https://docs.byteplus.com/en/docs/agentkit/What_is_AgentKit)
- [Install AgentKit CLI](https://docs.byteplus.com/en/docs/agentkit/Installing_AgentKit_CLI)
- [Create a runtime with the CLI](https://docs.byteplus.com/en/docs/agentkit/Creating_runtime_via_CLI_tool)
- [Platform service commands](https://docs.byteplus.com/en/docs/agentkit/Platform_service_commands)
- [AgentKit API overview](https://docs.byteplus.com/en/docs/agentkit/Overview)
- [Service address](https://docs.byteplus.com/en/docs/agentkit/Service_address)
- [Creating tools](https://docs.byteplus.com/api/docs/agentkit/Creating_tools)
- [Public-preview billing](https://docs.byteplus.com/en/docs/agentkit/Billing_instructions_during_public_preview)
- [Related cloud products](https://docs.byteplus.com/en/docs/agentkit/Related_cloud_products)
