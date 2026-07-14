---
name: byteplus-cloud
description: "Plan, provision, deploy, inspect, and troubleshoot applications on BytePlus using the official bp CLI, BytePlus Cloud Control Terraform provider, Edge Functions nest CLI/MCP, and product SDKs. Use for BytePlus architecture selection, authentication, infrastructure changes, application deployment, ModelArk Seed/Seedream/Seedance, Seed Speech TTS, TOS, ECS, VPC, VKE, veFaaS, API Gateway, databases, monitoring, or migration work."
---

# BytePlus Cloud

Operate BytePlus from a coding-agent workspace. Treat this skill as an orchestration and safety layer over current official tools, not as a frozen API catalog.

Resolve `<skill-dir>` to the directory containing this file.

## Apply the operating contract

1. Retrieve before relying on memory. Confirm current flags, action names, schemas, regions, limits, quotas, pricing, and product availability from live official sources.
2. Use only the capability currently exposed by an official CLI, provider schema, SDK, API, or product MCP. Never infer that a console control is programmable.
3. Establish the exact BytePlus profile, account identity, region, project, and environment before any remote mutation. Never silently use an ambient production target.
4. Inspect current resources before proposing changes. Prefer reuse or import over duplicate creation.
5. Separate planning from execution. Show the target, current state, changes, cost/security effects, verification, and rollback before consequential operations.
6. Keep credentials out of prompts, source files, manifests, command arguments, logs, and tool output. Never print `~/.byteplus/config.json`, `~/.nest.json`, or secret-bearing environment variables.
7. Verify every mutation through a fresh read, health probe, or product status check. Do not treat a successful command exit as proof that the application works.
8. Leave reproducible state: prefer Terraform for persistent multi-resource infrastructure and record non-secret resource mappings for imperative deployments.
9. Prefer agent-executable interfaces over console instructions. Never send the
   developer to the console for an operation exposed by a verified CLI, provider,
   SDK, or API. If a documented UI-only prerequisite remains, such as product
   activation, terms, billing setup, or service-role consent, identify the single
   minimal step and resume the automated workflow afterward.

## Load only the required references

- Read [sources.md](references/sources.md) before using exact API, schema, limit, price, region, or installation claims.
- Read [services.md](references/services.md) when selecting products or checking whether `bp`, Terraform, `nest`, an SDK, or an MCP is the right interface.
- Read [cli.md](references/cli.md) before installing, authenticating, discovering, or invoking `bp`.
- Read [iac.md](references/iac.md) before creating or changing Terraform/OpenTofu configuration.
- Read [edge-functions.md](references/edge-functions.md) before using `nest` or the official Edge Functions MCP.
- Read [vefaas-functions.md](references/vefaas-functions.md) before creating,
  releasing, invoking, exposing, troubleshooting, or deleting Function Service
  event functions and web applications.
- Read [cloud-sandbox.md](references/cloud-sandbox.md) before creating a veFaaS
  sandbox application or instance, executing a sandbox workload, handling a
  WebShell endpoint, or cleaning up sandbox resources.
- Read [ecs-vpc.md](references/ecs-vpc.md) for VM, network, security-group,
  load-balancer, private-deployment, and bounded end-to-end ECS-over-SSH work.
- Read [databases.md](references/databases.md) before provisioning or connecting to managed MySQL, PostgreSQL, or SQL Server.
- Read [vke.md](references/vke.md) for Kubernetes and Container Registry deployments.
- Read [modelark.md](references/modelark.md) for endpoint lifecycle, Seed text,
  Seedream image, or Seedance video integration and bounded smoke tests.
- Read [seed-speech.md](references/seed-speech.md) for text-to-speech activation,
  application credentials, resource selection, generation, and verification.
- Read [tos.md](references/tos.md) for buckets and objects; TOS is not available through the verified `bp`/Cloud Control baseline.
- Read [observability.md](references/observability.md) for logs, metrics, alarms, VMP, and post-deployment diagnosis.
- Read [agentkit.md](references/agentkit.md) only when building or operating an AgentKit application.
- Read [operations.md](references/operations.md) for deployment, verification, troubleshooting, rollback, cleanup, and project-manifest workflows.
- Read [security.md](references/security.md) before any remote mutation, IAM/networking change, public exposure, billable resource, secret operation, or deletion.

## Follow the end-to-end workflow

### 1. Classify the request

Distinguish among:

- architecture or documentation advice;
- read-only account inspection;
- local application changes;
- infrastructure planning;
- remote provisioning or deployment;
- troubleshooting;
- rollback or deletion.

Do not mutate remote state for a review, explanation, audit, or diagnosis-only request.

### 2. Inspect the workspace

Identify the runtime, framework, ports, build command, health endpoint, data stores, secrets, network requirements, traffic pattern, availability target, and existing IaC. Preserve the user's current deployment conventions when they are sound.

Check for existing BytePlus artifacts such as Terraform files, `nest.json`, deployment scripts, CI workflows, SDK configuration, and a `byteplus.project.yaml` manifest. Never overwrite an existing manifest or IaC layout without understanding it.

### 3. Diagnose the local toolchain

Run the local read-only doctor:

```bash
python3 <skill-dir>/scripts/byteplus_doctor.py --json
```

Add `--profile NAME --region REGION --check-auth` only when an authenticated identity check is needed. The doctor redacts credential-like fields. The STS call does not mutate cloud resources, but `bp` may refresh and cache temporary OAuth/SSO credentials as part of normal authentication.

Resolve the operational CLI only with `command -v bp`. A binary under `/tmp`,
`/private/tmp`, another OS temporary directory, or a test/build staging directory is
only a validation artifact; never reuse or report it as the developer's installed
`bp`.

If `bp` is missing and the requested task needs account inspection, provisioning,
deployment, or troubleshooting, inspect a verified persistent installation plan:

```bash
python3 <skill-dir>/scripts/install_bp.py --dry-run --dest "$HOME/.local/bin"
```

Then follow one of these branches instead of silently continuing with a temporary
binary:

- If the user already authorized installing the skill's required local tooling,
  install the exact version from the reviewed plan into the persistent user
  directory. Prefer an independently obtained `--sha256` pin. Without one,
  disclose that the official archive and checksum share one trust channel and use
  `--trust-official-release` only within the user's installation authorization.
- Otherwise, pause the operational workflow and ask whether the verified BytePlus
  CLI may be installed at `$HOME/.local/bin/bp`. Show the destination and source;
  do not make the user infer what prerequisite is missing.
- If the request is explicitly planning/documentation-only or forbids local
  installation, do not install. State that `bp` is unavailable and give the exact
  persistent install command as the next step.

The installer permits `latest` only for dry-run discovery. An actual installation
requires an exact version plus either an independently obtained digest or explicit
acceptance of the official-release trust channel. It verifies the published
SHA-256 checksum and does not execute the downloaded binary. After installation,
run `$HOME/.local/bin/bp version`. If that
directory is not on `PATH`, use the persistent absolute path for the current task
and tell the user how to add it; do not edit shell startup files without permission.

### 4. Establish the target

Require or discover all of:

- profile name and authentication mode;
- account identity;
- region;
- environment such as development, staging, or production;
- project/tagging convention;
- budget or size constraint when the change can incur cost.

For `bp`, prefer explicit per-invocation target flags:

```bash
bp sts GetCallerIdentity ---profile <profile> ---region <region>
```

Treat caller privilege as risk context, not as an authentication failure or an
operation class. A console-login profile that resolves to the BytePlus root
account is an accepted local-developer fast path. Warn once for that
profile/account/region, then continue requested read-only work and apply the
effect-based gates in [security.md](references/security.md) to each mutation. Do
not require the developer to create an IAM user in the console before bounded
development work, and do not request another approval solely because the caller
is root. Offer least-privilege hardening as an optional workflow; require it only
when the user's policy or target environment requires it.

Root caller status never replaces the normal effect-based gates: an already
requested bounded private development change can proceed under the disclosed plan,
while production, public exposure, IAM/networking, prepaid or unbounded cost,
replacement, and destructive actions retain their exact-plan approval gates.

When authentication setup or caller privilege is itself at issue, present these
paths without turning all three into prerequisites:

- **Quick local (default):** keep the current `bp login` profile, including a root
  profile, and use effect-based gates. This requires browser authorization but no
  IAM-console provisioning.
- **Hardened local (optional):** after explicit IAM-change approval, use the live
  IAM APIs to provision a scoped user, policy, project grant, or role. State that
  both IAM actions and STS `AssumeRole` are programmatic. Explain that
  restricted-user OAuth still needs one user-controlled browser sign-in and that
  raw access-key or `AssumeRole` responses cannot enter the agent transcript; do
  not promise seamless role switching without a tested credential-isolating
  helper.
- **Managed team (optional):** use Cloud Identity SSO when an organization already
  administers accounts, roles, and permission sets. One-time administration may be
  required, but SSO is not a prerequisite for solo local development.

When the developer specifically asks whether console work is required, lead with
the answer: quick local use needs only the browser OAuth authorization, not IAM
console provisioning. Then summarize the optional hardened-IAM and SSO paths in no
more than a few sentences, including any remaining user-controlled browser step or
credential-isolation limitation. Name IAM and STS as programmatic surfaces and
retain the effect-based gate summary above. Do not bury this answer inside the
deployment plan.

Before finishing an authentication or console-burden answer, check that it says:

1. quick local use does not require IAM-console provisioning;
2. root is valid but privileged and receives one warning, not a blanket block;
3. any IAM bootstrap is optional and requires explicit approval of the IAM changes;
4. IAM and STS are programmatic, but credentials must not enter the transcript;
5. restricted-user OAuth retains a user-controlled browser sign-in; and
6. Cloud Identity SSO is optional for teams and may require one-time administration.

Do not run an interactive login on the user's behalf without warning. For browser login, direct the user to `bp login`; for headless environments, use the documented remote flow. A non-default console-login profile is not automatically made current, so keep using explicit flags.

### 5. Select the control surface

Use the narrowest official interface that supports the task:

- Use `nest` or the Edge Functions MCP for Edge Functions and Pages workflows.
- Use BytePlus Cloud Control Terraform for supported, persistent multi-resource infrastructure when its authentication constraints are satisfied.
- Use `bp` for discovery, read operations, imperative control-plane actions, and gaps in Cloud Control.
- Use a current official product SDK or documented compatible tool for specialized data-plane operations such as TOS object transfer or ModelArk inference.
- Use an existing repository's working IaC or deployment tooling when it is safer and already authoritative.

Do not assume a universal BytePlus MCP or a universal Wrangler-like application CLI exists.

### 6. Discover live capability and schemas

Before composing a `bp` call, run:

```bash
bp --help
bp <service> --help
bp <service> <action> --help
```

For machine-readable discovery, use the bundled read-only wrapper:

```bash
python3 <skill-dir>/scripts/bp_catalog.py services
python3 <skill-dir>/scripts/bp_catalog.py actions <service>
python3 <skill-dir>/scripts/bp_catalog.py describe <service> <action>
```

The wrapper parses the installed CLI's help; it does not repair missing required-field, enum, permission, or regional metadata. Official action documentation remains required before a mutation.

Confirm the action's semantics in current official documentation. For Terraform, inspect the current Registry documentation and installed provider schema. For an SDK, inspect the installed package types and official versioned reference.

If no official programmable surface exposes the operation, report that limitation. Do not substitute a similarly named Volcano Engine API or an undocumented console endpoint.

### 7. Produce a change plan

Include:

- explicit account/profile, region, environment, and project;
- resources to reuse, create, update, replace, or delete;
- chosen interface and why it covers the operation;
- dependency order and expected outputs;
- cost, quota, public-access, IAM, networking, and data-loss effects;
- local file changes;
- verification checks;
- rollback or cleanup steps;
- unresolved assumptions.

Treat the user's request as authorization only for ordinary changes clearly necessary to the stated target. Request explicit confirmation before destructive replacement, deletion, production IAM/networking changes, public exposure, expensive compute/database/GPU capacity, or any material expansion of scope. Do not ask again when the user has already approved the exact disclosed plan.

### 8. Execute with a read-before-write discipline

For direct actions:

1. Read current state.
2. Confirm the target and live request schema.
3. Use an idempotency token where the API supports one.
4. Apply project/environment tags where supported.
5. Invoke the exact action with structured arguments.
6. Poll asynchronous operations with bounded retries.
7. Read state again and compare it with the plan.

For complex `bp` requests, use `--body` with one JSON object or array and do not mix it with flattened API parameters. Do not put secrets in the body or shell history. Remember that the fixed CLI flags use three hyphens: `---profile`, `---region`, and `---endpoint`.

For Terraform:

1. Pin a currently verified provider version.
2. Run formatting and validation.
3. Save a plan file.
4. Review replacements, deletions, sensitive values, and cost-bearing resources.
5. Apply the reviewed plan file, not a newly recalculated plan.
6. Verify application behavior after infrastructure convergence.

### 9. Deploy and verify the application

Verify at three levels:

- **Control plane:** resource status, configuration, region, network attachment, and identifiers.
- **Data plane:** health endpoint, expected request/response, storage or database access, and required model/API calls.
- **Operations:** logs, metrics, alarms, deployment history, and rollback availability.

Capture non-secret outputs needed by the application. If the repository needs an agent-readable resource map, copy [byteplus.project.yaml](assets/byteplus.project.yaml) and adapt it without storing credentials or treating it as authoritative cloud state.

### 10. Hand off clearly

Report:

- the target account/profile, region, and environment;
- files changed;
- resources created or changed and their non-secret IDs;
- commands or plans executed;
- verification evidence;
- remaining cost, security, quota, or manual steps;
- rollback and cleanup instructions.

## Handle failures deliberately

- Stop on profile, account, region, permission, schema, quota, or pricing ambiguity before mutation.
- Preserve request IDs and sanitized error codes.
- Do not blindly retry create or delete operations; first determine whether the earlier call partially succeeded.
- Use bounded backoff for documented eventual consistency only.
- For partial deployment, inventory actual state and propose convergence or cleanup before continuing.
- Enable CLI debug logging only when needed, sanitize the result, and never expose credentials or full request bodies containing secrets.

## Use the optional official Edge Functions MCP

Copy [mcp.edge-functions.json](assets/mcp.edge-functions.json) only when the host supports MCP configuration and the task uses Edge Functions. Query MCP `tools/list` after startup and treat that live result as the capability contract; continue to use current CLI help for unsupported lifecycle commands. Do not present it as an account-wide BytePlus control-plane MCP.
