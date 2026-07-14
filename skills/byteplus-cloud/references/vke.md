# VKE and Container Registry

Use this workflow for containerized applications that need Kubernetes. VKE is a multi-service, billable architecture; do not choose it for a small workload merely because the repository has a Dockerfile.

```text
Container Registry
→ build/tag/scan image
→ VPC/subnets/security
→ VKE cluster and node pools
→ kubeconfig credential
→ Kubernetes/Helm deployment
→ rollout, health, logs, metrics
```

## Current sources

- [VKE quick guide](https://docs.byteplus.com/en/docs/vke/Quick-guide)
- [Create a cluster](https://docs.byteplus.com/en/docs/vke/Creating-a-cluster)
- [VKE API actions](https://docs.byteplus.com/en/docs/vke/List-of-API-actions)
- [Use VKE with kubectl](https://docs.byteplus.com/en/docs/vke/Using-Vital-Kubernetes-Engine-with-kubectl)
- [Manage access credentials](https://docs.byteplus.com/en/docs/vke/Managing_access_credentials)
- [Push and pull Container Registry images](https://docs.byteplus.com/en/docs/cr/push-and-pull-images)
- [Container Registry access credentials](https://docs.byteplus.com/en/docs/cr/Get-access-credentials)

Discover installed actions:

```bash
bp cr --help
bp vke --help
```

Cloud Control also has VKE and CR resources; prefer it for persistent cluster infrastructure when the current schemas support the required configuration.

## Plan before creating

Confirm:

- why Kubernetes is appropriate versus Edge Functions, veFaaS, or ECS;
- region, zones, VPC/subnets, pod/service network ranges, and network mode;
- control-plane/API exposure and authorized source CIDRs;
- Kubernetes version and upgrade policy;
- node instance types, count, autoscaling, GPU needs, disk types, and images;
- registry ownership, image retention, vulnerability scanning, and pull authorization;
- ingress/load balancer, EIP/NAT, DNS, TLS, persistent volumes, and backups;
- system add-ons, observability, policy, and workload identity;
- total cluster/node/load-balancer/NAT/storage cost.

Network choices can be difficult or impossible to change. Retrieve current constraints before choosing CIDRs or modes.

## Credential handling

Kubeconfigs and registry authorization tokens are secrets.

- Do not print or commit output from `CreateKubeconfig` or `GetAuthorizationToken`.
- Write kubeconfig with restrictive permissions to an ignored temporary path and delete it when no longer needed.
- Prefer short-lived credentials and least-privilege service accounts/workload identities.
- Never embed registry tokens in Kubernetes YAML. Create/update the supported secret through a secure channel.
- Redact events/logs that echo environment secrets.

## Deployment procedure

1. Inspect existing registry, repositories, clusters, node pools, add-ons, and kubeconfigs.
2. Build a reproducible image, run tests, pin a content digest, and scan it.
3. Push to the intended registry/repository without returning the auth token.
4. Plan/apply VPC, cluster, node pools, and add-ons.
5. Poll cluster and nodes to ready states.
6. Obtain short-lived access securely and verify `kubectl cluster-info`/permissions.
7. Render and review Kubernetes or Helm output before applying.
8. Apply to an explicit namespace/context.
9. Watch rollout; inspect events, probes, logs, services, ingress, and endpoints.
10. Run a health/behavior smoke test and verify monitoring.

Always show the current Kubernetes context and namespace before a write or delete. Avoid `kubectl apply -f` against generated/unreviewed remote content.

## Cleanup

Deleting a cluster may not remove registry images, load balancers, EIPs, volumes, snapshots, DNS, or application data. Enumerate ownership and dependents. Preserve backups and required logs before deletion.
