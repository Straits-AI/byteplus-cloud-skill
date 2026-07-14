# Function Service (veFaaS) deployment workflow

Use this reference for regional Function Service event functions, web
applications, releases, triggers, execution logs, and exact cleanup. Edge
Functions are a separate CDN product; use [edge-functions.md](edge-functions.md)
for those workloads.

## Contents

- [Choose the function shape](#choose-the-function-shape)
- [Discover the live contract](#discover-the-live-contract)
- [Deploy a bounded event function](#deploy-a-bounded-event-function)
- [Verify all three layers](#verify-all-three-layers)
- [Treat public HTTP as a separate deployment](#treat-public-http-as-a-separate-deployment)
- [Clean up exactly](#clean-up-exactly)
- [Know what the tested baseline proves](#know-what-the-tested-baseline-proves)

## Choose the function shape

Route from the application's process and invocation model:

| Requirement | veFaaS shape |
|---|---|
| Event, timer, queue, or object-triggered handler | Event function |
| HTTP server or container listening on a port | Web application |
| Long-running batch entry point | Task function |
| Stateful, explicitly managed temporary execution environment | Cloud Sandbox; read [cloud-sandbox.md](cloud-sandbox.md) |

Confirm the target region supports the selected shape. Keep functions private by
default. A timer-trigger smoke test proves event execution; it does not prove an
HTTP deployment.

## Discover the live contract

Inspect the installed CLI before composing a request:

```bash
bp vefaas --help
bp vefaas CreateFunction --help
bp vefaas GetRevision --help
bp vefaas Release --help
bp vefaas GetReleaseStatus --help
bp vefaas CreateTimer --help
bp vefaas ListFunctionInstances --help
bp vefaas GetFunctionInstanceLogs --help
bp vefaas DeleteTimer --help
bp vefaas DeleteFunction --help
```

Then retrieve the current official action pages, runtime development/deployment
guide, available regions, limits, and pay-as-you-go prices. The CLI help is useful
for shape discovery but does not reliably expose every required field, enum,
regional restriction, or side effect.

Before mutation, record:

- explicit profile, masked account, region, project, and development/production
  environment;
- deterministic run prefix and tags;
- runtime, handler, package or image source, memory/CPU, timeout, concurrency, VPC,
  public-egress, logging, and IAM-role choices;
- expected invocation path and unique non-secret verification marker;
- current price class, maximum scale, resource lifetime, and cleanup owner;
- exact IDs and create/delete request IDs as they are returned.

Do not copy a signed source-upload or source-download URL into a ledger, transcript,
manifest, or debug log. Treat it as a credential-bearing URL under
[security.md](security.md).

## Deploy a bounded event function

Use this sequence for a small code-package smoke deployment. Re-read every action
schema immediately before use.

### 1. Package and inspect locally

1. Implement the current runtime's documented handler signature.
2. Include a unique non-secret marker in the expected invocation output or log.
3. Build the ZIP with the handler at the documented package root.
4. Inspect the archive listing and run local unit tests.
5. Keep dependencies within the current package/source limits.

Do not place secrets, BytePlus profiles, `.env` files, private keys, or unrelated
workspace files in the archive.

### 2. Inventory before create

List functions by the deterministic name and stable run tag. If a matching
function exists, determine ownership and either reuse, update, import, or stop.
Never retry `CreateFunction` until a fresh list proves the first request did not
create a resource.

Build one structured `--body` from the live schema. For a private elastic event
function, explicitly review at least:

- `Name`, `Runtime`, `SourceType`, and `Source`;
- `MemoryMB`, CPU setting, request timeout, and concurrency;
- VPC and shared-internet-access flags;
- log-delivery settings, project, role, and tags.

Use the smallest current specification that satisfies the test, cap elastic
instances in the release plan, and avoid enabling VPC, public egress, reserved
instances, or Log Service merely to make a smoke test pass.

Write the returned function ID and create request ID to the run ledger immediately.
When reading the function back, remove `Source`, `SourceLocation`, credentials, and
signed URLs before emitting output.

### 3. Release deterministically

1. Read draft revision `0` with `GetRevision` and compare runtime, resource,
   network, log, source-type, and handler configuration with the plan.
2. Call `Release` for that exact revision with an explicit target traffic weight,
   rolling step, and bounded maximum instance count.
3. Record the release record ID.
4. Poll `GetReleaseStatus` with bounded backoff until the documented terminal
   state.
5. Require the stable revision and traffic state to match the plan. A successful
   `Release` response alone is not deployment proof.

### 4. Invoke through a real trigger

For an event-function smoke test, create one run-owned timer only after retrieving
the current timer schema and cron semantics. Give it a deterministic name, zero or
the smallest approved retry count, and a payload containing the non-secret marker.

Record the timer ID immediately. Wait through a bounded trigger window, then query
the exact function instance and its bounded log window. Require the marker to
appear in a real runtime invocation. Delete the timer as soon as the evidence is
captured; do not leave a one-minute timer running for convenience.

## Verify all three layers

### Control plane

- Freshly read the function and draft/stable revision without exposing source
  locations.
- Require the release status, stable revision, traffic weight, maximum scale,
  runtime, region, network, and log settings to match the plan.
- Require a function instance to reach the documented ready state for the tested
  revision.

### Data plane

- Invoke through the intended trigger or route.
- Require an exact status/result or unique marker produced by the deployed code.
- Exercise one bounded failure input when the application contract requires it.

### Operations

- Retrieve a bounded, sanitized instance-log window and correlate it with the
  invocation marker or request ID.
- Record release history and the last-known-good revision.
- Verify trigger inventory and any configured metrics/alarms. Record the
  intentional omission of persistent monitoring for a short disposable test.

## Treat public HTTP as a separate deployment

Do not translate a successful timer invocation into “the HTTP function is
deployed.” Public HTTP requires a current supported web-application or API Gateway
path, plus separate approval for public exposure and gateway cost.

Before making an HTTP claim:

1. Retrieve the current veFaaS web-application or APIG-trigger documentation and
   live `bp apig`/provider schemas.
2. Plan the gateway, service, upstream, route, authentication, domain, path, port,
   TLS, and network dependencies.
3. Obtain exact approval for the public endpoint and all persistent/billable
   gateway resources.
4. Create only supported gateway types; do not infer a serverless request body
   from a standard-gateway schema.
5. Probe the resulting URL from the intended client network and require the
   deployed marker.
6. Verify gateway access logs/metrics and record rollback and cleanup ownership.

If this complete path has not run, state that the function is privately deployed
and trigger-verified, while public HTTP remains unverified.

## Clean up exactly

Cleanup is destructive. Use it only when it was approved in the disposable-run
plan or after resource-specific approval.

1. Stop new traffic and delete run-owned timers, queue/object triggers, and APIG
   routes first.
2. Freshly list triggers and require no run-owned trigger remains.
3. Delete the exact function ID.
4. Poll until both an exact-ID read and a stable name/tag query show absence.
5. Remove any run-owned APIG upstream, service, and gateway in documented
   dependency order; preserve reused gateway/network resources.
6. Remove local ZIPs and temporary build directories that contain deployment
   payloads.
7. Update the run ledger with delete request IDs and fresh absence checks.

Report cleanup as `CLEAN` only when every run-owned function, trigger, route, and
local sensitive artifact is absent. A successful delete response without a fresh
read is not enough.

## Know what the tested baseline proves

The July 2026 developer-account baseline proved this private path end to end with
the official CLI: code-package creation, draft inspection, release, stable revision,
timer invocation, exact marker in instance logs, trigger deletion, function
deletion, and fresh absence checks.

It did not prove a public HTTP route, every runtime, every trigger type, VPC
attachment, Log Service delivery, GPU functions, reserved capacity, or production
rollout. Revalidate the current account, region, CLI, API, prices, and schemas
before each deployment.

## Official sources

- [Function Service documentation](https://docs.byteplus.com/en/docs/faas/)
- [Getting started with function deployment](https://docs.byteplus.com/en/docs/faas/FaaS_Quick_Start)
- [Create an event function](https://docs.byteplus.com/en/docs/faas/Creating_event_functions)
- [Function configuration](https://docs.byteplus.com/en/docs/faas/Function_configuration)
- [CreateFunction API](https://docs.byteplus.com/en/docs/faas/CreateFunction)
- [Release API](https://docs.byteplus.com/en/docs/faas/Release)
- [GetReleaseStatus API](https://docs.byteplus.com/en/docs/faas/GetReleaseStatus)
- [CreateTimer API](https://docs.byteplus.com/en/docs/faas/CreateTimer)
- [GetFunctionInstanceLogs API](https://docs.byteplus.com/en/docs/faas/GetFunctionInstanceLogs)
- [DeleteFunction API](https://docs.byteplus.com/en/docs/faas/DeleteFunction)
- [Trigger overview](https://docs.byteplus.com/en/docs/faas/Trigger_overview)
- [Pay-as-you-go billing](https://docs.byteplus.com/en/docs/faas/Pay-as-you-go)
