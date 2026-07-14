# Deployment and operations workflow

Use this reference for end-to-end deployment, troubleshooting, rollback, and cleanup.

## Convert an application into requirements

Inspect rather than ask the user for facts already present in the repository:

- runtime, CPU/GPU, memory, process model, and architecture;
- build artifact or container image;
- listening port and health endpoint;
- static assets and object storage;
- database, cache, queue, or model dependencies;
- inbound/outbound networking and DNS;
- environment variables and secrets;
- background jobs, cron, and long-running tasks;
- scaling, availability, data durability, and recovery objectives;
- CI/CD and current IaC.

Ask only for decisions that materially change architecture, cost, data location, public exposure, or production risk.

## Write a concise plan

Use this structure:

```text
Target
- profile/account:
- region:
- environment/project:

Current state
- existing resources and ownership:

Proposed changes
- create/update/replace/delete:
- local file changes:
- dependency order:

Effects
- estimated cost class:
- public/network/IAM/data implications:

Execution
- tool and exact plan/commands:
- asynchronous waits:

Verification
- control plane:
- data plane:
- observability:

Rollback/cleanup
- previous version/state:
- cleanup order:
```

Do not claim an exact cost without retrieving current pricing and enough configuration to calculate it.

## Preserve idempotence and ownership

- Query by resource ID and stable project tags, not name alone when names are not unique.
- Use deterministic environment-qualified names.
- Adopt existing resources through Terraform import or an explicit manifest rather than recreating them.
- Use API idempotency tokens where documented.
- Record whether each resource is managed by Terraform, `bp`, `nest`, an SDK, or a human process.
- Never let two mechanisms believe they own the same mutable resource.

## Use the project manifest

Copy `assets/byteplus.project.yaml` to the project root only when no equivalent application map exists. Adapt it to record intent and non-secret outputs.

The manifest is not cloud state and must not contain:

- access keys, tokens, passwords, API keys, or signed URLs;
- full secret values or secret-manager payloads;
- Terraform state;
- unverified resource IDs.

Reconcile it against live state at the start of future deployments.

## Verify in layers

### Control plane

- target account, project, region, and environment match;
- resource reaches the documented ready state;
- networking, encryption, backups, and deletion protection match the plan;
- resource IDs and endpoints are captured without secrets.

### Data plane

- application responds on the intended route;
- health/readiness checks pass;
- database, storage, queue, and model calls work with least privilege;
- negative/error behavior does not expose sensitive data;
- deployment works from the intended client network.

### Operations

- logs and metrics arrive;
- alarms cover the agreed failure modes;
- deployment/version history exists;
- rollback inputs are recorded;
- a cold restart or new replica can recover where relevant.

## Troubleshoot systematically

1. Reproduce the smallest failing request.
2. Confirm profile, identity, region, endpoint, and API version.
3. Confirm live schema and required parameters.
4. Capture sanitized error code and request ID.
5. Inspect resource state and dependent-resource state.
6. Check IAM denial, quota, availability, eventual consistency, network path, and service status.
7. Change one variable at a time.
8. Re-run verification after the fix.

Do not enable broad permissions merely to test. Do not retry a create call until checking whether it succeeded remotely.

## Roll back safely

- Prefer product versions/rollback for application code when available.
- For Terraform, create and review a new plan that converges to the prior desired configuration.
- For database or storage changes, verify backup/restore semantics before touching data.
- For networking or IAM, preserve access needed to complete rollback.
- For partial deployment, inventory actual resources and dependency order before cleanup.

## Clean up deliberately

List every resource and dependency to be removed. Confirm resource-specific data retention, snapshots, backups, public endpoints, and ongoing billing. Require explicit authorization for destructive cleanup even when the original deployment failed.

After cleanup, verify absence through fresh List/Describe/Get calls and update non-secret manifests/state ownership records.
