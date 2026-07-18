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
was initially redirected from the AgentKit console to a `Talk to an expert`
beta-product page with no activation control. Treat that state as an entitlement
blocker. After BytePlus enabled the same account, the documented create path
worked without changing the account identity, region, or OAuth login. Do not
submit a sales/contact request, message an external party, or create IAM, CR, TOS,
or ModelArk dependencies to bypass a missing entitlement.

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

Also run `agentkit config --show` inside the project. AgentKit CLI 0.7.13 generated
a project whose persisted cloud provider was `volcengine` even when the process
environment selected BytePlus. Require the displayed project provider and region
to be BytePlus values before build or deploy; do not rely on environment variables
alone.

## Reuse `bp login` without exposing credentials

Do not assume the AgentKit CLI natively reads a `bp login` profile. The tested
AgentKit CLI baseline documented AK/SK configuration, while the official BytePlus
Go SDK exposes `clicreds.CliProvider` for resolving an existing named BytePlus CLI
profile.

A live July 2026 test proved that `clicreds.CliProvider` could use a console-login
OAuth profile to sign AgentKit OpenAPI requests. It also proved that an isolated
parent process could resolve temporary credentials in memory and provide them
only to an AgentKit CLI child process. With AgentKit CLI 0.7.13, the child also
required `AGENTKIT_CLOUD_PROVIDER=byteplus` and the explicit BytePlus region;
otherwise the CLI defaulted to Volcano Engine. No AK/SK was printed or persisted.

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

The initial July 2026 developer-account test reached exactly this state:
OAuth-signed `ListRuntimes` and `ListTools` succeeded, while documented create
actions returned `InvalidActionOrVersion`; final inventories remained zero. After
BytePlus enabled AgentKit on the account, a repeat test created and invoked a
minimal sandbox successfully. This confirms that the earlier result was an
entitlement boundary rather than an invalid OAuth or endpoint implementation.

## Deploy an agent runtime

Only continue after service activation and the exact IAM/networking/cost plan are
approved.

### Validate the generated application locally

Treat `agentkit init` as scaffolding, not proof that its unconstrained dependency
set currently resolves to a runnable application. In a live 16 July 2026 check,
AgentKit CLI/SDK 0.7.13 generated an A2A template whose `agentkit-sdk-python>=`
constraint resolved with `a2a-sdk` 1.1.0, while the installed AgentKit SDK still
imported the A2A 0.3 server modules. Pinning only A2A then exposed a second missing
runtime dependency because the template left `google-adk` commented out.

For that tested SDK baseline, this compatible local set passed the package
resolver, health route, agent-card route, and one A2A `message/send` call:

```text
agentkit-sdk-python==0.7.13
a2a-sdk==0.3.7
google-adk==1.32.0
opentelemetry-api==1.37.0
opentelemetry-sdk==1.37.0
```

These are evidence pins, not permanent recommendations. Before using them, inspect
the current package metadata and generated requirements, resolve in an isolated
environment, and run the package manager's consistency check. If newer official
versions have corrected the dependency graph, prefer the current compatible set
and record it in the run ledger.

Before any cloud build or registry creation, require all of the following locally:

1. the process starts on an unused explicit port;
2. `GET /ping` returns an exact non-secret marker;
3. `GET /.well-known/agent-card.json` returns the intended card and protocol;
4. a real A2A `message/send` request returns the exact marker; and
5. the process exits cleanly and leaves no listener behind.

Use a deterministic no-model executor for platform acceptance where possible. It
isolates runtime packaging and protocol behavior from ModelArk activation, model
availability, API-key handling, latency, and inference charges. A separate
model-backed acceptance is still required before claiming model integration.

The first `agentkit build` may appear quiet while Docker downloads the official
AgentKit base image. Confirm the generated `FROM` registry is the current official
BytePlus regional registry, then use bounded Docker pull/build diagnostics rather
than assuming a deadlock or substituting an unreviewed base image. Record the
resolved image digest used for a managed deployment. Check host and Docker storage
capacity before the pull: the tested Python 3.12 base expanded to approximately
2.27 GB before application and build-cache layers. Remove only images, containers,
and caches owned by the current run; never use a broad prune on a shared developer
machine.

Do not equate Container Registry `public endpoint: Enabled` with immediate Docker
readiness. The tested registry control plane reported enabled before the exact
domain resolved and bypassed the local Docker proxy path. Poll the registry
`/v2/` endpoint from the same network namespace used by Docker until it returns
the expected unauthenticated response, then log in and push. If a narrowly scoped
temporary DNS or proxy exception is required, record its original state, limit it
to the exact registry domain, and revert it after the run.

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

An interrupted or timed-out `agentkit deploy` can create the remote runtime before
the CLI persists its ID locally. Before retrying, list runtimes by the deterministic
run name and reconcile the existing ID; a blind retry can fail with a duplicate
name while leaving the original resource behind. Treat raw runtime objects as
secret-bearing because a successful key-auth runtime may include its API key and
endpoint. Emit only a sanitized state summary.

If a runtime reaches `Error` at version 0 with no endpoint or API key, preserve its
safe status and artifact metadata, delete that exact runtime, and verify absence.
Do not repeatedly recreate it without a new diagnosis. Also inspect generated
defaults before creation: the tested CLI requested a minimum replica of 1 and
enabled APM-related runtime settings even though the application did not request
observability. These defaults can affect cost and dependencies.

Do not treat runtime creation as deployment success. Verify control plane, data
plane, and operations independently.

## Deploy an AgentKit sandbox tool

AgentKit managed tools and veFaaS Cloud Sandbox are distinct products. For an
AgentKit All-in-one or Skills Sandbox workflow:

An All-in-one (AIO) Sandbox is the smallest documented AgentKit proof after
entitlement. The public API documentation describes this class as All-in-one,
while AgentKit CLI 0.7.13 accepts `CodeEnv`; retrieve the current installed schema
and use its exact value. It does not require a customer Container Registry image,
ModelArk endpoint, TOS mount, or runtime service role. The lowest tested proof is
one run-tagged tool at 2,000 millicores and 4,096 MiB, no TOS, no private network,
a generated API key kept out of output, one 60-second session, and one benign
shell marker.

1. Retrieve the current `CreateTool`, `CreateSession`, invocation, and delete
   schemas and supported tool types.
2. Confirm required service roles and policies. Current Skills Sandbox guidance
   may require TOS access; do not grant it to an unrelated tool.
3. Select the smallest current CPU/memory, shortest session TTL, and no
   storage/VPC. AgentKit CLI 0.7.13 rejects both public and private network access
   being disabled; a no-VPC `CodeEnv` therefore uses an authenticated public
   endpoint. Disclose this boundary before creation.
4. Create the tool, record its ID, poll ready, create one short session, and run a
   benign marker workload.
5. Verify tool configuration, session result, logs/status, and a bounded failure
   case.
6. Delete the session, tool, and run-owned IAM/storage dependencies, then require
   fresh zero-result inventories.

Do not emit raw tool or session objects. In the tested 0.7.13 CLI,
`agentkit tools show --output json` returned the generated API key in plaintext,
and `agentkit tools session list --fields ...` still emitted credential-bearing
session endpoints. Capture those results inside a credential-isolating process,
redact complete API keys and signed endpoint query strings, and output only safe
IDs, status, shape, timestamps, and request IDs. Deleting the tool invalidates its
generated key.

The live 16 July 2026 acceptance created one `CodeEnv` tool, reached `Ready`,
created a 60-second session, observed the exact marker
`bpskill-agentkit-ok`, deleted the probe session and tool, and then obtained fresh
`ListTools=0` and `ListRuntimes=0`. This is live AIO Sandbox evidence; it is not yet
evidence for a custom AgentKit runtime deployment.

The same acceptance also built and pushed a deterministic A2A image through the
official CLI to a run-owned BytePlus Container Registry. Two managed runtime
creates were accepted but ended at `Error`, version 0, without an endpoint or API
key. Both runtimes and the repository, namespace, and registry were deleted, and
fresh inventories were zero. Keep this classified as live partial until a managed
runtime reaches ready and returns the exact marker through its real endpoint.

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
