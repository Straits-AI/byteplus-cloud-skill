# Torch Object Storage (TOS)

TOS is a product-specific exception to the general `bp`/Cloud Control path.

At the verified baseline:

- `bp` has no `tos` service;
- the current `bytepluscc` provider has no TOS resource family;
- the older `byteplus` Terraform provider's TOS resources are marked unmaintained.

Use the current official TOS SDK/API for application integration and bucket configuration. Use `tosutil` for object transfer, inspection, batch operations, diagnostics, and presigned URLs.

## Retrieve current tooling

- [tosutil guide](https://docs.byteplus.com/en/docs/tos/tosutil)
- [tosutil common commands](https://docs.byteplus.com/en/docs/tos/Common-commands)
- [TOS SDK overview](https://docs.byteplus.com/api/docs/tos/SDK-overview)
- [TOS API overview](https://docs.byteplus.com/api/docs/tos/reference-api-overview)
- [CreateBucket](https://docs.byteplus.com/en/docs/tos/reference-createbucket)
- [Regions and endpoints](https://docs.byteplus.com/en/docs/tos/region-and-endpoint)

Install `tosutil` only from the current official download page and verify any published checksum. Inspect live help before using commands:

```bash
tosutil version
tosutil help
tosutil help <command>
```

Do not assume `tosutil` consumes a `bp login` profile. Follow its current documented credential flow, using a dedicated least-privilege identity or temporary credentials where supported. Never show its configuration file.

## Bucket plan

Before creation, decide and verify:

- globally unique name, region, and flat vs hierarchical namespace type;
- private access by default;
- server-side encryption and key ownership;
- versioning, object lock/retention, lifecycle, and backup/replication;
- CORS, custom domain, TLS, logging, event notifications, and transfer acceleration;
- application IAM policy and cross-account access;
- expected storage, request, retrieval, and egress costs.

Do not set a public ACL or public bucket policy merely to make a test pass. Use a signed URL, application proxy, CDN origin configuration, or narrowly scoped policy when appropriate.

## Safe object operations

Read/list/stat operations can normally run against the confirmed bucket. Treat these as high risk:

- recursive `rm` or deletion with versions/delete markers;
- lifecycle expiration or replication changes;
- ACL/policy changes;
- bucket deletion;
- cross-region bulk copy;
- generating long-lived presigned URLs;
- retention/object-lock configuration, which may be irreversible.

For uploads:

1. Confirm the destination bucket, region, and key prefix.
2. Avoid overwriting an existing key unless intended.
3. Use multipart/resume for large files when documented.
4. Verify object size, checksum/ETag semantics, metadata, encryption, and access.

For deletion, list the exact keys/versions first, show the deletion set, and verify afterward. Emptying a bucket may delete application data even when deleting the bucket itself fails.

## Declarative gap

If a stack uses Terraform for everything else, isolate TOS provisioning in a documented script or module boundary. Store only non-secret outputs and make the operation idempotent. Record that TOS is not Terraform-managed so later agents do not run `terraform destroy` expecting it to remove the bucket/data.
