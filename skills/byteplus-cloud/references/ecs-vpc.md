# ECS and VPC deployment workflow

Use this reference for VM, VPC, security-group, EIP, SSH, load-balancer, and
private-deployment work.

## Contents

- [Choose the deployment path](#choose-the-deployment-path)
- [Discover live capability](#discover-live-capability)
- [Plan an ECS deployment](#plan-an-ecs-deployment)
- [Run the bounded ECS-over-SSH workflow](#run-the-bounded-ecs-over-ssh-workflow)
- [Verify all three layers](#verify-all-three-layers)
- [Clean up without touching reused resources](#clean-up-without-touching-reused-resources)
- [Handle partial failures](#handle-partial-failures)
- [Know what the tested baseline proves](#know-what-the-tested-baseline-proves)

## Choose the deployment path

Treat compute and networking as one dependency graph:

```text
identity/region
-> VPC and route tables
-> subnet/zone
-> security group
-> image, instance type, stock, key/role
-> ECS instance
-> optional EIP/load balancer/DNS
-> application configuration
-> health, logs, and metrics
```

Prefer BytePlus Cloud Control Terraform for persistent stacks. Use `bp ecs` and
`bp vpc` for discovery, documented dry runs, diagnostics, and supported
operational actions. Use the imperative SSH workflow below only for a bounded
development deployment, a bootstrap test, or a task whose current Cloud Control
surface is insufficient.

Keep an application instance private by default. A disposable EIP plus restricted
SSH is acceptable only when public reachability is required and the exact public
exposure, source CIDRs, billing mode, lifetime, and cleanup have been approved.
For production, prefer a load balancer, bastion, managed command path, or private
connectivity over exposing an administrative port.

## Discover live capability

Inspect the installed catalog before composing a request:

```bash
bp ecs --help
bp vpc --help
bp ecs DescribeRegions --help
bp ecs DescribeZones --help
bp ecs DescribeAvailableResource --help
bp ecs DescribeInstanceTypes --help
bp ecs DescribeImages --help
bp ecs RunInstances --help

python3 <skill-dir>/scripts/bp_catalog.py find KeyPair --service ecs
python3 <skill-dir>/scripts/bp_catalog.py find SecurityGroup --service vpc
python3 <skill-dir>/scripts/bp_catalog.py find Eip --service vpc
```

Retrieve current official semantics before mutation:

- [ECS API reference](https://docs.byteplus.com/en/docs/ecs/API-Reference)
- [RunInstances](https://docs.byteplus.com/en/docs/ecs/RunInstances)
- [ECS security guidance](https://docs.byteplus.com/en/docs/ecs/How-to-enhance-the-security-of-ECS-instances)
- [VPC API reference](https://docs.byteplus.com/en/docs/vpc/API-Reference)
- [CreateVpc](https://docs.byteplus.com/en/docs/vpc/CreateVpc)
- [CreateSubnet](https://docs.byteplus.com/en/docs/vpc/CreateSubnet)
- [CreateSecurityGroup](https://docs.byteplus.com/en/docs/vpc/CreateSecurityGroup)

Do not copy request bodies from this reference. Confirm current required fields,
enums, idempotency support, asynchronous states, regional stock, pricing, and
deletion behavior from the live CLI and official action pages.

## Plan an ECS deployment

Resolve these inputs before mutation:

- explicit profile, caller account, region, environment, and deterministic run
  prefix;
- application artifact, architecture, port, health route, service user, and
  startup mechanism;
- VPC/subnet ownership, zone, route and egress requirements;
- private-only access or approved public path;
- exact SSH and application source CIDRs;
- compatible image, smallest adequate instance type, count, disks, bandwidth, and
  billing mode;
- data persistence, deletion protection, backup/snapshot, and disk-on-delete
  behavior;
- expected resource lifetime, cleanup owner, and destructive-cleanup approval.

Never authorize `0.0.0.0/0` or `::/0` for SSH, RDP, databases, or an internal
application port. If the developer's source address is dynamic, stop and obtain a
new exact CIDR instead of widening the rule.

Inventory resources by ID and stable tag. Reuse a VPC or subnet only after
confirming ownership and policy. Record reused resources separately and mark them
`do not delete`. Treat an EIP, system disk, and running or stopped instance as
potentially billable until current product documentation and final deletion state
prove otherwise.

Before the first create call, open a sanitized run ledger containing:

```text
run prefix / tag:
profile / masked account / region / environment:
approved exposure and source CIDRs:
approved cost class and lifetime:

reused resources (never delete):
- type / ID / ownership evidence

created resources (delete only these exact IDs):
- type / ID / create request ID / cleanup action / state

implicit resources:
- ENI / system volume / delete-with-instance expectation

verification:
- control plane / data plane / operations

cleanup:
- action / request ID / absence check
```

Write each returned resource ID to the ledger immediately after creation. Never
depend on a later name search to reconstruct cleanup ownership.

## Run the bounded ECS-over-SSH workflow

### 1. Inventory and preflight

1. Verify the explicit caller and region.
2. Describe existing VPCs, subnets, security groups, instances, EIPs, key pairs,
   ENIs, and volumes matching the stable run tag or intended dependencies.
3. Describe zones, available stock, instance types, and public images. Select a
   compatible image and the smallest adequate available instance type; verify the
   image supports the intended initialization and SSH path.
4. Retrieve current pay-as-you-go pricing, quota, balance/coupon behavior, EIP
   metering, system-volume behavior, and bandwidth choices. A billing preflight is
   evidence, not a guarantee that the later create will succeed.
5. Build the exact `RunInstances` body and run `DryRun=true` when the current action
   documents it. Treat a documented `DryRunOperation` response as request
   validation only; it creates no instance and does not prove capacity at the
   later execution time.

### 2. Create ephemeral SSH material

Use a mode-`0700` temporary directory, `umask 077`, a dedicated private/public key
pair, and a dedicated `known_hosts` file. Import only the public key. Record the
cloud key-pair ID immediately, but never print, upload, commit, or retain the
private key after cleanup.

Do not disable host-key checking or write the ephemeral host into the developer's
global `known_hosts`. For a one-use development host, bind the first accepted host
key to the dedicated file after confirming the EIP-to-instance association. For a
production host, require a trusted host-key fingerprint or a managed access path.

### 3. Create the network boundary

1. Create a dedicated security group in the selected VPC.
2. Authorize TCP/22 only from the approved operator CIDR.
3. Authorize the application port only from the approved probe/client CIDR, or
   leave it private when a load balancer will front it.
4. Read the security group back and compare the complete ingress set with the
   plan. Account for the provider's default egress rule explicitly.
5. Allocate the smallest approved EIP/bandwidth only when required. Use a
   documented-safe description and a stable idempotency token.

Do not create the instance until the security group is in its documented usable
state and the ingress comparison passes.

### 4. Create and attach the instance

1. Submit one idempotent `RunInstances` request with the selected subnet/zone,
   image, instance type, dedicated security group, imported key pair, explicit
   disk behavior, pay-as-you-go billing, count, and stable tags.
2. Record the instance ID before polling.
3. Poll with bounded backoff until the documented ready state. Record the implicit
   primary ENI and system-volume IDs and whether each is configured to delete with
   the instance.
4. Associate the recorded EIP only after the instance is ready.
5. Read the EIP back and require it to point to the exact instance before SSH.

Never write BytePlus account credentials onto the VM. Use an instance role for
cloud API access when the application actually needs it.

### 5. Deploy over SSH

Use `BatchMode=yes`, a bounded connection timeout, the dedicated identity file,
and the dedicated `known_hosts` file. Retry only expected boot/SSH readiness with
a bounded deadline; fail on authentication or host-key mismatch.

Transfer a reviewed application artifact and a reviewed, non-secret setup script.
Install into an application-specific directory, run the service as an unprivileged
user, and use the image's service manager for restart behavior. Do not pass secrets
in SSH command arguments or return secret-bearing remote output. Use a protected
secret mechanism when the application requires credentials.

Start the service and require the local VM health endpoint to return the expected
status and content before probing through the public address or attaching a load
balancer.

## Verify all three layers

Do not claim deployment success until all applicable checks pass.

### Control plane

- Freshly describe the instance and require the expected `RUNNING` state, billing
  mode, subnet, security group, key pair, ENI, system volume, and EIP.
- Freshly describe the EIP and require a normal attached state pointing to the
  expected instance.
- Freshly describe all security-group rules and require only the approved ingress
  CIDRs/ports plus the acknowledged default egress behavior.

### Data plane

- Authenticate through SSH with only the ephemeral imported key.
- Probe the health endpoint locally on the VM.
- Probe it from the intended external or private client vantage point and compare
  both status and a stable response marker.
- Do not infer that a security-group read proves packet flow.

### Operations

- Require the service manager to report the application active under the intended
  unprivileged user.
- Inspect a bounded, sanitized log window.
- Record restart count and unexpected failures.
- Add agreed metrics and alarms for persistent deployments; a short disposable
  test may record their intentional omission.

## Clean up without touching reused resources

If cleanup was approved as part of the disposable-run plan, execute it against
only the exact IDs in the run ledger. Otherwise obtain resource-specific approval
before deletion.

Use dependency order:

1. Stop traffic and detach load-balancer/DNS dependencies when present.
2. Disassociate the EIP and poll until it is available and has no target.
3. Delete the exact ECS instance and poll until both an ID query and the stable run
   tag query return zero instances.
4. Verify the implicit primary ENI is absent.
5. Verify the system volume is deleted, or handle it according to the approved
   retention plan. Do not assume `DeleteWithInstance` worked without a fresh read.
6. Delete the dedicated security group only after instance/NIC dependencies are
   gone.
7. Delete the imported cloud key pair.
8. Release the EIP; disassociation alone does not end EIP ownership or billing.
9. Query every created type again by exact ID and by stable run tag/name, and
   require zero results.
10. Re-read reused VPC/subnet resources and confirm they remain available.
11. Remove the local private key, public key, dedicated `known_hosts`, and their
    temporary directory.

Report cleanup as `CLEAN` only when every recorded cloud resource is absent, every
reused resource remains intact, and all ephemeral local key material is gone.
Mention that delayed metering can still produce a small charge for the period in
which pay-as-you-go resources existed.

## Handle partial failures

- Capture sanitized error codes and request IDs.
- After any failed create, query by idempotency token where supported, exact ID,
  and stable tag before retrying. A nonzero CLI exit does not prove no resource was
  created.
- Reuse the same documented idempotency token for an uncertain duplicate request.
  Use a new token only after fresh reads prove the rejected request created no
  resource and the corrected request is intentionally distinct.
- Do not continue to instance creation when the network boundary, key import, EIP,
  quota, balance, stock, or dry-run validation is unresolved.
- On cleanup failure, keep the ledger open, preserve the remaining exact IDs, and
  retry only after inspecting dependency state. Never broaden a delete query to
  all resources sharing a human-readable name.

## Know what the tested baseline proves

A live disposable test with `bp` v1.0.17 in `ap-southeast-1` proved this bounded
path end to end:

- reuse an existing VPC/subnet without deleting them;
- select available x86 stock and an Ubuntu image;
- validate `RunInstances` with documented dry-run behavior;
- import an ephemeral RSA-2048 public key;
- restrict TCP/22 and the application port to one `/32` source;
- create a pay-as-you-go ECS instance and attach a low-bandwidth EIP;
- authenticate with SSH, install an unprivileged system service, and pass local
  plus external health probes;
- verify instance, EIP, security-group, ENI, volume, and service-manager state;
- delete the instance and all run-owned dependencies while preserving reused
  networking.

This proves the workflow, not universal product availability. Revalidate every
schema, region, stock, image, price, quota, and asynchronous state on each run.
