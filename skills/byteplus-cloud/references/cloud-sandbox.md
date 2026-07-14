# veFaaS Cloud Sandbox workflow

Use this reference to create a sandbox application, release it, start a bounded
sandbox instance, execute a real workload, and remove every run-owned resource.
Cloud Sandbox is stateful for the instance lifetime and is billed for that
lifecycle; it is not an ordinary event-function invocation.

## Contents

- [Understand the resource graph](#understand-the-resource-graph)
- [Discover the live contract](#discover-the-live-contract)
- [Create and release a sandbox application](#create-and-release-a-sandbox-application)
- [Create and exercise one bounded instance](#create-and-exercise-one-bounded-instance)
- [Handle the RunCode and WebShell boundary](#handle-the-runcode-and-webshell-boundary)
- [Verify all three layers](#verify-all-three-layers)
- [Keep public HTTP out of the private claim](#keep-public-http-out-of-the-private-claim)
- [Clean up exactly](#clean-up-exactly)
- [Know what the tested baseline proves](#know-what-the-tested-baseline-proves)

## Understand the resource graph

Treat Cloud Sandbox as two lifecycle layers plus an optional ingress layer:

```text
sandbox application (veFaaS FunctionType=sandbox)
-> released stable revision
-> sandbox instance (explicit lifetime/spec/image)
-> private WebShell or separately approved APIG route
```

Creating a sandbox instance requires the ID of a released sandbox application. An
ordinary event-function ID is not interchangeable; the service rejects it.

The sandbox application's source image supplies application defaults. An instance
request can supply current supported image, command, port, environment, resource,
and lifetime overrides. Resolve which layer owns each value and verify the final
instance rather than assuming inheritance.

## Discover the live contract

Inspect the installed catalog and current official docs:

```bash
bp vefaas --help
bp vefaas CreateFunction --help
bp vefaas GetRevision --help
bp vefaas Release --help
bp vefaas GetReleaseStatus --help
bp vefaas GetPublicSandboxImageGroups --help
bp vefaas ListSandboxImages --help
bp vefaas CreateSandbox --help
bp vefaas DescribeSandbox --help
bp vefaas ListSandboxes --help
bp vefaas SetSandboxTimeout --help
bp vefaas KillSandbox --help
bp vefaas GenWebshellEndpoint --help
bp vefaas RunCode --help
```

Retrieve current regional availability, lifecycle billing, minimum/maximum CPU,
memory and timeout, image commands and ports, release semantics, quota, and public
ingress requirements. A CLI action appearing in help is discovery evidence only;
it does not prove that the target service version implements it.

Inventory existing sandbox applications and instances before create. Open a run
ledger with the deterministic name/tag, explicit profile/account/region/project,
approved price class and maximum lifetime, application/function ID, release record
ID, sandbox ID, request IDs, and exact cleanup owner.

## Create and release a sandbox application

### Select a current image

1. Call `GetPublicSandboxImageGroups` and `ListSandboxImages` with the current
   public-image enum.
2. Select an official image in the target region whose pre-cache status is
   successful.
3. Retrieve the image's current startup command, listening port, supported
   workload protocol, and resource recommendation from official documentation.
4. Do not substitute a similarly named Volcano Engine image or control-plane
   endpoint. A BytePlus-returned public image record is acceptable even when its
   backend registry hostname reflects shared infrastructure.

### Treat help-omitted fields as tested-but-live-revalidate

In the tested `bp` v1.0.17 baseline, `CreateFunction --help` omitted
`FunctionType` and `Port`, while a structured raw `--body` accepted both through
the public BytePlus API. `GetRevision` then returned the expected sandbox type and
port.

This is **tested-but-live-revalidate**, not a permanent schema guarantee:

1. Re-read current `CreateFunction` documentation, API Explorer metadata, SDK
   types, CLI version/help, and release notes.
2. Stop if the current official surfaces disagree about these fields or the target
   region.
3. Use one structured body only after validation; do not mix it with flattened
   parameters.
4. Immediately sanitize and read draft revision `0` back. Require
   `FunctionType: sandbox`, the intended `Port`, `Runtime: native/v1`, image source,
   CPU strategy, resource limits, VPC/public-network state, and tags.
5. If the type or port did not take effect, inventory partial state, delete only
   the exact run-owned function after approval, and stop.

The application body must be derived live. Review at least the deterministic
name, `native/v1` runtime, sandbox function type, image source type and source,
startup command, port, CPU strategy, memory/CPU, concurrency, timeout, VPC/public
egress, logs, project, role, and tags.

Do not enable public routing, VPC access, reserved warm capacity, mounts, roles, or
log delivery unless the workload requires them and their cost/security effects
were approved.

### Release the exact draft

1. Record the application/function ID returned by `CreateFunction` immediately.
2. Read draft revision `0` and compare it with the plan.
3. Call `Release` for that exact revision with explicit traffic, rolling step, and
   maximum instance count.
4. Record the release record ID and poll `GetReleaseStatus` with a deadline.
5. Require the documented terminal success state and stable revision before
   creating a sandbox instance.

## Create and exercise one bounded instance

Build the current `CreateSandbox` body with:

- exact sandbox application Function ID;
- shortest approved platform lifetime and the smallest current CPU/memory that
  can run the image;
- bounded request timeout and concurrency;
- official pre-cached image ID/address, current startup command, and listening
  port;
- non-secret stable run metadata;
- no mounts, environment secrets, public exposure, or network expansion unless
  explicitly required.

Write the returned sandbox ID to the ledger immediately. Poll `DescribeSandbox`
with bounded backoff. Require `Ready`, the expected application ID, stable revision,
image ID/address, command, port, resource specification, metadata, instance type,
and expiry. Stop and clean up on `Failed`; retain the sanitized error code, message,
and request ID.

Execute one benign marker workload with a bounded timeout. Do not install large
dependencies or run arbitrary user-supplied shell text merely to prove the data
plane. Capture only the expected marker and sanitized status, not a full terminal
transcript.

## Handle the RunCode and WebShell boundary

### Do not rely on the advertised RunCode action

The tested CLI listed `bp vefaas RunCode`, but the BytePlus service returned
`InvalidActionOrVersion` for the CLI-selected API version. Treat that mismatch as
a current server/catalog gap. Preserve the sanitized error and request ID, and do
not retry different versions or endpoints by guessing.

Re-test only when current official release notes or action documentation show a
supported contract. The existence of CLI input fields `FunctionId`, `SandboxId`,
and `Data` does not establish a working data plane.

### Protect GenWebshellEndpoint as a secret-bearing path

`GenWebshellEndpoint` is a documented Function Service action that returns a
temporary WSS endpoint containing a ticket. Treat the complete endpoint as a
secret/signed URL:

- capture `bp` stdout in a credential-isolating process and parse the endpoint in
  memory;
- pass it directly to the WebSocket client without printing it, placing it in a
  command argument, persisting it, or adding it to the run ledger;
- emit only connection status, the expected marker, sanitized request ID, and
  timeout/error class;
- close the WebSocket promptly and discard the endpoint;
- never include the URL in debug logs, shell tracing, screenshots, CI artifacts,
  issue reports, or deployment summaries.

The tested WebShell frame shape used JSON client input with `Op: stdin` and JSON
server output with `Op: stdout`. That frame protocol is not described on the
official endpoint-generation page. Treat it as tested-but-live-revalidate: validate
one fixed benign no-op/marker with a deadline, never interpolate untrusted command
text, and stop if the live frame contract differs.

If no reviewed credential-isolating WebSocket client is available, do not expose
the endpoint to improvise one in chat. Classify direct workload execution as
blocked, terminate the sandbox, and report that control-plane deployment alone was
verified.

## Verify all three layers

### Control plane

- Require the application draft and stable revision to identify a sandbox function
  with the expected image, command, port, region, network posture, and maximum
  scale.
- Require the sandbox instance to be `Ready` with the expected revision, image,
  resource bounds, metadata, and expiry.

### Data plane

- Execute one benign command or request through a currently supported private
  path and require the exact marker.
- Use a separately approved APIG route only when public access is part of scope.
- Do not count WebSocket connection success without command output as execution
  proof.

### Operations

- Record release status/history and bounded startup or instance logs when the
  current product exposes them safely.
- Preserve sanitized action request IDs and terminal sandbox status.
- Confirm the explicit timeout/expiry protects against an abandoned test, while
  still performing immediate cleanup rather than waiting for TTL.

## Keep public HTTP out of the private claim

Creating and exercising a private sandbox does not create a public URL. A private
WebShell execution is not public HTTP. Current
BytePlus guides describe API Gateway service/route configuration for public
sandbox access. That is a separate billable and security-sensitive deployment.

Do not claim public HTTP until the agent has:

1. retrieved current APIG gateway-type and route schemas;
2. obtained approval for the exact public exposure and gateway cost;
3. created or reused explicitly owned gateway, service, upstream, route,
   authentication, domain, and TLS configuration;
4. probed the public endpoint and exact sandbox instance routing behavior; and
5. verified access logs/metrics and cleanup or rollback.

A rejected serverless-gateway request does not prove that the product lacks
serverless APIG; it proves only that the attempted request was invalid. Do not fall
back to a materially larger standard gateway without a new exact plan and approval.

## Clean up exactly

Cleanup is destructive and must be part of the approved disposable plan or receive
resource-specific approval.

1. Stop new ingress and delete run-owned APIG routes before terminating instances.
2. Call `KillSandbox` for each exact sandbox ID.
3. Poll `DescribeSandbox`/`ListSandboxes` until the instance is absent or reaches
   the documented terminal state. Do not treat `Terminating` as final absence.
4. Delete the exact sandbox application Function ID only after instance cleanup,
   unless current documentation defines application deletion as the approved
   cascading cleanup path.
5. Poll `ListFunctions` by exact ID and stable name/tag until it returns zero.
6. Remove only run-owned APIG upstream, service, gateway, domain, or auth resources
   in documented dependency order; preserve reused resources.
7. Remove local temporary payloads and any in-memory client state; verify no signed
   WebShell endpoint was persisted.
8. Record kill/delete request IDs and fresh absence results.

After an application is deleted, `ListSandboxes` may return `ResourceNotFound` for
the old Function ID instead of an empty list. Accept that only as the final
application-level absence check when `KillSandbox` was already accepted and the
exact function deletion plus zero-result name/tag query are verified. Do not use a
pre-delete `ResourceNotFound` or a missing list permission as cleanup proof.

Report `CLEAN` only when every run-owned instance, sandbox application, trigger,
route/gateway resource, and local secret-bearing artifact is absent.

## Know what the tested baseline proves

The July 2026 developer-account baseline proved this private path end to end:

- create a sandbox application through public `CreateFunction` with live-validated
  raw fields;
- read back sandbox type/port, release revision `1`, and reach release completion;
- create the smallest current short-lived instance from an official pre-cached
  image and reach `Ready`;
- execute a benign marker through a secret-isolated WebShell connection;
- call `KillSandbox`, delete the application, and verify fresh absence.

It did not prove public APIG routing, a stable `RunCode` action, an officially
documented WebShell frame protocol, arbitrary/custom images, mounts, VPC access,
warm pools, browser/computer sandboxes, production observability, or every region.

## Official sources

- [Cloud Sandbox documentation](https://docs.byteplus.com/en/docs/faas/Cloud_sandbox)
- [Sandbox applications](https://docs.byteplus.com/en/docs/faas/Sandbox_applications)
- [Sandbox images](https://docs.byteplus.com/en/docs/faas/Sandbox_images)
- [CreateSandbox API](https://docs.byteplus.com/en/docs/faas/CreateSandbox)
- [ListSandboxes API](https://docs.byteplus.com/en/docs/faas/ListSandboxes)
- [DescribeSandbox API](https://docs.byteplus.com/en/docs/faas/DescribeSandbox)
- [SetSandboxTimeout API](https://docs.byteplus.com/en/docs/faas/SetSandboxTimeout)
- [KillSandbox API](https://docs.byteplus.com/en/docs/faas/KillSandbox)
- [ListSandboxImages API](https://docs.byteplus.com/en/docs/faas/ListSandboxImages)
- [GenWebshellEndpoint API](https://docs.byteplus.com/en/docs/faas/GenWebshellEndpoint)
- [Fast deploying SandboxFusion](https://docs.byteplus.com/en/docs/faas/Fast_deploying_SandboxFusion_code_sandbox)
- [veRL integration with Cloud Sandbox](https://docs.byteplus.com/en/docs/faas/veRL_integration_with_veFaaS_cloud_sandbox)
- [Function Service pay-as-you-go billing](https://docs.byteplus.com/en/docs/faas/Pay-as-you-go)
