# Validation matrix

This document defines exactly what the public-preview label means. It deliberately
separates live end-to-end evidence from documentation, schema, and planning
coverage.

## Evidence levels

- **Live E2E:** a disposable resource or task was created where applicable, the
  workload was invoked through its real data plane, control/data/operations proof
  was collected, and exact cleanup was freshly verified.
- **Live partial:** authentication or read paths were exercised, but a named
  entitlement, product, public-route, or cost boundary prevented full creation.
- **Guidance:** the skill retrieves current official sources and provides a
  reviewed runbook, but this project has not yet completed live acceptance for the
  path.

## Acceptance baseline

- Date: 13–16 July 2026
- CLI: official BytePlus `bp` 1.0.17
- Region: `ap-southeast-1`
- Authentication: local OAuth-derived BytePlus profile
- Safety: smallest practical disposable resources, no prepaid purchases, exact
  ownership ledger, and deletion/deactivation after each test

Raw ledgers contain account and infrastructure identifiers and are retained
privately. This public document records capability-level outcomes only.

## Capability results

| Area | Level | What was proved | Remaining boundary |
|---|---|---|---|
| CLI bootstrap | Live E2E | Missing-CLI detection, checksum-verified persistent install, version check, service/action discovery | Revalidate when BytePlus changes release packaging |
| OAuth profile | Live E2E | Browser login, temporary profile reuse, signed identity/read calls | Repeat with least-privilege and Cloud Identity profiles |
| ECS/VPC | Live E2E | PAYG instance, dedicated `/32` security rules, ephemeral SSH key, EIP, unprivileged app, external health check, full dependency cleanup | Multi-instance, load balancer, private-only, and production patterns remain guidance |
| veFaaS function | Live E2E | Event function, release, timer-triggered invocation marker, logs, trigger/function cleanup | This did not prove a public HTTP route |
| API Gateway | Live partial | Current schema and rejected minimal gateway attempt were observed; account inventory remained clean | Complete a supported bounded public route and external probe |
| Cloud Sandbox | Live E2E | Sandbox application, release, shortest bounded instance, private WebShell command, kill/delete/absence | Private WebShell is not public HTTP |
| ModelArk text | Live E2E | One current Seed response with bounded output and secret-isolated temporary key | Revalidate volatile model ID and pricing every run |
| Seedream | Live E2E | One image, in-memory decode, metadata/digest verification, no retained artifact | Broader image workflows remain guidance |
| Seedance 1.5 | Live E2E | One shortest bounded silent video, polling, media verification, task deletion, model deactivation | Seedance 2.0 prepaid path was intentionally excluded |
| Seed Speech TTS 2.0 | Live E2E | One short TTS request, terminal code, decoded MP3 metadata/digest, service restored inactive | Additional voices, streaming clients, and deployed credential rotation remain guidance |
| AgentKit AIO Sandbox | Live E2E | OAuth-reused `CodeEnv` tool at 2 vCPU/4 GiB, 60-second session, exact shell marker, session/tool deletion, fresh zero inventories | Custom managed runtime, release, model-backed agent, and runtime artifact path remain unvalidated |
| AgentKit A2A runtime application | Live partial | Deterministic app passed local health/card/A2A calls; official build pushed a run-owned CR image; two managed creates were accepted but ended at `Error`, version 0, without endpoint/key; exact runtime/repository/namespace/registry cleanup and zero inventories were verified | Managed readiness, release, remote invoke, and runtime logs remain unvalidated |
| Edge Functions | Guidance | Current `nest` CLI/MCP workflow and safety rules | No live `nest` deployment in this acceptance run |
| Cloud Control Terraform | Guidance | Provider/source routing and plan/apply safety model | No full live Terraform stack acceptance |
| TOS | Guidance | Product/API routing and secret/data boundaries | Not present in the verified generic CLI/Cloud Control baseline; no live bucket test |
| VKE/CR | Guidance | Cluster, registry, kubeconfig, and deployment runbook | No live cluster or application acceptance |
| Managed databases | Guidance | Product selection, network, secret, migration, backup, and cleanup runbooks | No live database provisioning acceptance |
| Observability | Guidance | Product-specific logs/metrics routing and three-layer proof model | No unified cross-product observability acceptance |

## Public-preview release gate

The project may be released publicly when:

1. the skill and all bundled scripts pass offline tests and structural validation;
2. the public tree contains no credentials, raw live-test ledgers, generated
   media, Terraform state, or account-specific artifacts;
3. every claim is scoped to the evidence level above; and
4. known blockers remain visible in the README and issue tracker.

## Stable 1.0 direction

A stable 1.0 should add repeatable, sanitized acceptance for a custom AgentKit
runtime, public HTTP/APIG, Edge Functions, persistent Terraform infrastructure,
and the major guidance-only service branches that the project chooses to support. It
should also repeat core tests in more than one BytePlus account and credential
model, with a protected maintainer workflow for recurring live validation.

“Stable” will describe the supported workflows, not every BytePlus console
feature. Unsupported or console-only operations must remain explicit.
