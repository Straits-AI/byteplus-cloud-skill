# Observability and troubleshooting

Route by signal instead of looking for one universal BytePlus observability tool:

```text
Application/service logs       → Torch Log Service (TLS)
Cloud service metrics/alarms   → Cloud Monitor
Prometheus/Kubernetes metrics  → VMP
Immediate Kubernetes diagnosis → kubectl describe/events/logs
Edge behavior                  → Nest/Edge Functions product workflow
```

## Tool coverage

- `bp cloudmonitor` currently includes metric reads and alarm/configuration operations; discover live help.
- `bp vmp` includes workspace/alert configuration, but do not assume it supports every PromQL/data query.
- TLS is not a current `bp` service, though Cloud Control supports several TLS configuration resources. Use TLS API/SDK for query/data-plane work.
- Product-specific logs may require product APIs rather than a central command.

Sources:

- [Torch Log Service API overview](https://docs.byteplus.com/en/docs/tls/API-overview)
- [TLS operations](https://docs.byteplus.com/api/docs/tls/Operations)
- [TLS query overview](https://docs.byteplus.com/api/docs/tls/Query-overview-2)
- [Cloud Monitor API overview](https://docs.byteplus.com/en/docs/cloudmonitor/Overview-3)
- [VMP regions and availability zones](https://docs.byteplus.com/api/docs/vmp/Regions-and-availability-zones)

## Post-deployment verification

1. Confirm resource/workload health from its control plane.
2. Exercise a health endpoint and one representative request.
3. Correlate timestamps, request/task IDs, resource IDs, deployment version, and region.
4. Check application logs without dumping unrelated customer data.
5. Check platform events and error codes.
6. Query relevant metrics over a bounded time window.
7. Verify that alerts/dashboards target the new resource and environment.
8. Distinguish missing telemetry from a healthy system.

Never solve a monitoring failure by broadly opening security groups or IAM. Validate endpoint, network path, agent status, permissions, region, and resource dimensions separately.

## Data safety

- Bound log queries by environment, resource, and time.
- Do not return credentials, authorization headers, cookies, personal data, model prompts, or database contents found in logs.
- Avoid enabling verbose/debug logging in production without a time limit and rollback.
- Treat webhook URLs and alert destinations as potentially secret.
- Record query filters and evidence, not raw log dumps.

## VMP MCP warning

The BytePlus VMP MCP guide currently points to a Volcano Engine implementation whose default endpoint construction uses `volcengineapi.com` and a China region. Do not bundle or start it as though it were automatically compatible with an international BytePlus account.

Only use it after:

1. retrieving the current BytePlus VMP endpoint for the target region;
2. configuring an explicit endpoint supported by the implementation;
3. confirming no Volcano Engine credentials/regions are used;
4. passing read-only workspace and query tests in the target BytePlus account.

Until then, use verified BytePlus APIs/SDKs and `bp` actions.
