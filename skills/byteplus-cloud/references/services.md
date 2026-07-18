# Product and control-surface routing

Select from the application's requirements, then verify current availability in the target region and live tool catalogs.

## Compute and application runtime

| Requirement | Start with | Primary interface |
|---|---|---|
| JavaScript request logic close to CDN users | Edge Functions | `nest` / official Edge Functions MCP |
| Static site on the edge | Edge Functions Pages | `nest pages` after live help |
| General serverless function or container function | veFaaS | BytePlusCC when supported, otherwise `bp vefaas` / product API |
| Stateful, short-lived code/browser execution environment | veFaaS Cloud Sandbox | `bp vefaas` / current Function Service API; sandbox application plus explicit instance lifecycle |
| General VM or GPU host | ECS | BytePlusCC for persistent stacks; `bp ecs` for discovery/operations |
| Managed Kubernetes workload | VKE + CR | Terraform for cluster dependencies; `kubectl`/Helm for workloads |
| Managed API ingress | API Gateway or ALB/CLB | BytePlusCC or current `bp` service |
| Foundation-model inference | ModelArk (`ark`) | Runtime SDK/API for inference; `bp ark` or BytePlusCC for exposed control-plane resources |
| Agent platform workflow | AgentKit | Current AgentKit API/SDK/docs; do not assume `bp` coverage |

Choose the least operationally heavy runtime that satisfies language, process, networking, execution-time, state, GPU, scaling, and regional requirements. Do not force an arbitrary application into Edge Functions merely because it has the most complete MCP.

Do not treat an event function as a Cloud Sandbox application. A sandbox instance
requires a released sandbox-function application and explicit lifecycle controls.
Do not treat private WebShell execution as a public HTTP deployment; public sandbox
access has a separate API Gateway dependency and approval boundary.

## Storage and data

| Requirement | Start with | Primary interface |
|---|---|---|
| Object/blob storage | TOS | Official TOS SDK or documented S3-compatible tool |
| Relational MySQL/PostgreSQL/SQL Server | Managed RDS product | BytePlusCC or current `bp` service |
| Cache | Redis | BytePlusCC or `bp redis` |
| Document database | MongoDB | BytePlusCC or `bp mongodb` |
| Streaming/message service | Kafka/RabbitMQ/BMQ where available | BytePlusCC or current `bp` service |
| Search/analytics | Elasticsearch/ByteHouse/product service | Current product provider/API |

TOS is a critical exception to generic assumptions. The `bp` v1.0.17 catalog does not list a `tos` service, and the contemporaneous BytePlusCC provider does not expose a TOS bucket resource. Recheck current versions, then use the official TOS SDK or documented S3-compatible tooling. TOS requires regional S3 endpoints, Signature V4, and virtual-hosted style; not every S3 feature is compatible. Do not use a deprecated Terraform provider just to hide this gap.

## Networking and exposure

Map dependencies explicitly:

```text
VPC
├── subnets / route tables
├── security groups
├── NAT or public IP only when required
├── compute or VKE nodes
└── ALB/CLB/API Gateway/private endpoints
```

Use private connectivity by default. Treat these as high-risk changes requiring parameter-level review:

- `0.0.0.0/0` or `::/0` ingress;
- public IP allocation;
- internet-facing load balancers or gateways;
- route/NAT changes;
- cross-account or cross-region connectivity;
- certificate, DNS, CDN origin, and WAF changes.

## Observability

Use the product's current logging and monitoring surface rather than assuming one universal agent tool:

- CloudMonitor for supported metrics and alarms;
- VMP for Prometheus-compatible monitoring;
- TLS/Log Service where exposed by current product APIs/provider;
- deployment history and debugger facilities for Edge Functions;
- Kubernetes events/logs/metrics for VKE;
- health checks and application telemetry for every runtime.

The official VMP and Edge Functions MCP integrations are product-specific. Do not present them as unified BytePlus observability.

## Capability discovery algorithm

For every desired operation:

1. Search the installed `bp --help` catalog.
2. Search the current BytePlusCC Registry schema.
3. Search the official product docs and SDKs.
4. Confirm the target region and account entitlement.
5. Choose the interface with the best plan, state, and verification behavior.
6. If no official path exists, state the gap and stop before mutation.

Never equate broad coverage with universal coverage. Never use an undocumented console endpoint or a Volcano Engine implementation as a BytePlus substitute.

Before the first create for Kafka, KMS, or another managed product with activation
or cross-service dependencies, read [service-readiness.md](service-readiness.md).
Treat product activation, service-linked roles, region/AZ/spec stock, and
dependency-aware teardown as part of the service contract rather than as errors to
discover through repeated billable create calls.
