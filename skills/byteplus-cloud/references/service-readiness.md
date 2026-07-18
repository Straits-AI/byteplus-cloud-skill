# Managed-service readiness and opaque create failures

Use this reference before the first create for a managed queue, database, search,
KMS, or similar cross-service product, and whenever a schema-correct create returns
an opaque `400` or `500`.

An `InternalError` is a symptom, not a diagnosis. Do not keep changing billable
parameters until one request happens to work. A correct-looking request can still
fail because the product is inactive, a service-linked role is missing, an
availability/specification value is unavailable, a dependent resource is not
ready, or the service applies an undocumented value constraint.

## Run the first-use preflight

1. Establish the explicit profile, masked account, region, project, and
   environment. Inventory the target product and every dependency.
2. Inspect `bp <service> <action> --help`, but do not treat its type-only output as
   a complete schema. Retrieve the official action page, example request, error
   table, prerequisites, regions, specifications, and billing behavior.
3. Make the smallest documented read call with explicit pagination. An error such
   as `*_ServiceNotOpen`, `*NotActivated`, or `*NotEnabled` is a product-activation
   signal. Search the current CLI/API for an activation action once. If none
   exists, identify the single current account-owner UI step, wait for activation,
   then resume through the CLI/API.
4. Check the product's official access-control prerequisites. If it requires a
   service-linked role, read the exact role by name before creation. Inspect the
   live `bp iam CreateServiceLinkedRole --help`; where the service name is
   documented and the user approves the exact IAM mutation, create it
   programmatically and read it back. Otherwise ask the owner to perform only the
   documented consent step. Never grant a broad user policy merely to bypass the
   service-linked role.
5. Call the product's region, Availability Zone, specification, and quota discovery
   actions. Parameter names vary by API generation: use the exact action contract
   rather than converting `ZoneId` into `Zones` or guessing a compute code.
6. Build one JSON request from the official example, changing only reviewed values.
   Use one `--body` for non-secret object or array parameters. If the request
   contains a password or other secret and the CLI has no protected stdin/file
   input, use a credential-isolating official SDK client; do not put the secret in
   shell arguments, history, debug logs, or the run ledger.
7. Execute once with an idempotency token where supported. Record the sanitized
   error code and request ID. Before retrying, list by token/name/tag/ID and inspect
   billing orders to determine whether the request partially succeeded.

## Interpret common signatures

| Signature | Treat it as | Next check |
|---|---|---|
| `*_ServiceNotOpen`, `*NotActivated`, `*NotEnabled` | Product activation is absent | Current activation API; otherwise the minimal owner-controlled UI step |
| `InternalError` or opaque `500` on a validated first create | Unknown prerequisite or service defect, not permission to guess | Service-linked role, activation, dependency state, AZ/spec stock, value constraints, then support with request ID |
| `InvalidParameter` or opaque `400` | Request or value mismatch may be under-described | Official example, SDK type, discovery API, exact character/length rules |
| `OperationDenied.*NotEmpty` | Dependency-aware deletion is required | Enumerate and remove approved child resources before the parent |

If the same minimal request still fails after the documented prerequisite audit,
stop. Preserve its request ID, safe schema, dependency state, and retrieval date
for BytePlus support; do not perform a parameter lottery.

## Current verified first-use table

This table is deliberately small and must be revalidated before mutation.

| Product | Verified prerequisite or signal | Agent behavior |
|---|---|---|
| Message Queue for Kafka | Official first-use documentation requires the service-associated `ServiceRoleForKafka` so Kafka can access resources such as VPC. `bp` 1.0.17 exposes `iam GetRole` and `iam CreateServiceLinkedRole`. | Read `ServiceRoleForKafka`. If absent, review current trust/policy documentation and, after explicit IAM approval, use the current programmatic service-linked-role action when its service name is confirmed. Fall back to only the documented consent screen if the API path is unavailable. |
| KMS | Current quick start says the first console visit activates KMS and may take several minutes. `bp` 1.0.17 exposes KMS resource actions but no service-activation action. | On `KMS_ServiceNotOpen` or equivalent, ask the account owner to open KMS once, wait for activation, then repeat a read call. Never confuse `EnableKey` with enabling the KMS product. |
| ModelArk | Model activation and model access are separate from control-plane login. | Follow [modelark.md](modelark.md); do not guess model IDs or print API keys. |
| AgentKit | Account entitlement, agreement, service role, artifact, and runtime/tool lifecycles are distinct. | Follow [agentkit.md](agentkit.md) and stop before dependencies when create entitlement is absent. |
| Seed Speech | Product/application activation and its credential are separate from ModelArk and `bp` OAuth. | Follow [seed-speech.md](seed-speech.md). |

Do not generalize `ServiceRoleForKafka` into `ServiceRoleFor<Service>` and create
guessed roles. Service names, role names, trust policies, and whether an API path
exists are product-specific.

## Kafka-specific discovery and request rules

For the verified Kafka V2 (`2022-05-01`) contract:

- `DescribeInstances` is paginated and requires `PageNumber` and `PageSize`.
- `DescribeAvailabilityZones` takes `RegionId`; `CreateInstance` takes `ZoneId`.
- `Version`, `ComputeSpec`, `StorageType`, storage size, partitions, and stock must
  come from current official specifications and discovery results. The CLI help
  shows strings, not their valid values.
- `ChargeInfo` is a nested object. Do not use dotted flattened flags such as
  `--ChargeInfo.ChargeType`; construct one validated JSON body.
- `UserPassword` is secret-bearing and subject to current character and length
  constraints. Do not learn those constraints by sending variants. Retrieve the
  current rule/example, generate a conforming secret inside the protected client,
  and keep it out of command arguments and output.

## Tear Kafka down as a dependency graph

Deletion destroys data and always requires exact resource-specific approval.
Inventory first; the applicable graph can include topics, consumer groups,
connectors, ACLs, allowlists, users, public access, and an EIP.

For an approved disposable instance:

1. stop producers and consumers and verify retention/export decisions;
2. delete approved topics and groups plus other instance-owned children required
   by the current API, polling their absence;
3. call `DeletePublicAddress` and wait until the Kafka public attachment is absent;
4. delete the pay-as-you-go Kafka instance and poll to absence;
5. release only the run-owned EIP after it is detached; and
6. verify exact IDs are absent while preserving reused VPCs, subnets, and shared
   service-linked roles.

BytePlus documents that `DeletePublicAddress` unbinds but does not release the EIP,
and that `DeleteInstance` requires an empty instance. Do not reverse those steps or
treat an asynchronous delete acknowledgement as final cleanup.

## Current official sources

- [Kafka cross-service access authorization](https://docs.byteplus.com/api/docs/kafka/cross-service-authorization)
- [Kafka CreateInstance V2](https://docs.byteplus.com/en/docs/kafka/CreateInstance-v2)
- [Kafka DescribeInstances V2](https://docs.byteplus.com/api/docs/kafka/DescribeInstances-v2)
- [Kafka DescribeAvailabilityZones V2](https://docs.byteplus.com/en/docs/kafka/DescribeAvailabilityZones-v2)
- [Kafka DeleteInstance V2](https://docs.byteplus.com/en/docs/kafka/DeleteInstance-v2)
- [Kafka DeletePublicAddress V2](https://docs.byteplus.com/en/docs/kafka/DeletePublicAddress-v2)
- [KMS getting started](https://docs.byteplus.com/en/docs/kms/Getting_started_with_key_management)
