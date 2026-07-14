# Managed relational databases

Read this reference before provisioning or connecting an application to BytePlus RDS for MySQL, PostgreSQL, or SQL Server. Treat a database deployment as billable, stateful, and recovery-sensitive.

## Select and discover the interface

Prefer BytePlus Cloud Control Terraform for a persistent supported database stack when its authentication mode is compatible. The current provider catalog includes resource families for RDS MySQL, PostgreSQL, and SQL Server, but support differs by engine and version. Inspect the installed provider schema instead of copying a stale example.

For read-only discovery or an operation missing from Cloud Control, inspect the installed CLI:

```bash
bp rdsmysqlv2 --help
bp rdspostgresql --help
bp rdsmssql --help
```

Service names can change between CLI generations. Use `bp --help` and `bp_catalog.py find` rather than assuming the names above are present. Retrieve the current product API documentation before invoking an action.

Official entry points:

- [RDS for MySQL](https://docs.byteplus.com/en/docs/RDS_for_MySQL/about_rds_for_mysql)
- [RDS for PostgreSQL](https://docs.byteplus.com/en/docs/RDS_for_PG/)
- [RDS for SQL Server](https://docs.byteplus.com/en/docs/RDS_for_SQLServer/)
- [BytePlusCC provider](https://registry.terraform.io/providers/byteplus-sdk/bytepluscc/latest/docs)

## Inspect before planning

Establish:

- engine and supported version;
- existing instance, endpoint, database, account, allow-list, parameter template, backup, and replica resources;
- region, zones, VPC, subnet, DNS, and application network path;
- storage class and capacity, compute specification, node count, and billing mode;
- availability, maintenance, backup retention, recovery point, and recovery time requirements;
- encryption, audit, slow-query, metrics, and alarm requirements;
- connection-pool and maximum-connection expectations;
- migration, seed-data, and schema ownership.

Prefer private endpoints. Do not create a public database endpoint or broad allow-list for convenience. Restrict database ingress to the application security group or the narrowest documented network source.

## Plan state and recovery

Before approval, disclose:

- recurring compute, storage, backup, and network cost class;
- any prepaid commitment;
- replacement or downtime behavior;
- whether storage can be reduced or the engine/version can be downgraded;
- deletion protection and final-backup behavior;
- credential delivery and rotation mechanism;
- restore procedure and cleanup owner.

Do not apply a production parameter, engine-version, storage, topology, endpoint, or deletion change without retrieving its exact replacement and downtime semantics. Never treat a Terraform plan as a database backup.

## Keep credentials out of agent-visible state

- Create application database users with least privilege; do not use the administrative account at runtime.
- Store passwords in a protected secret system and inject them at runtime.
- Do not put passwords in Terraform source, committed variable files, the project manifest, shell arguments, logs, migration output, or health responses.
- Treat Terraform state and plan files as sensitive when the provider can return credentials or connection material.
- Prefer a non-secret connection descriptor containing only host, port, database name, TLS mode, and secret reference.

## Provision in dependency order

1. Read current engine, region, zone, specification, and quota availability.
2. Reuse or create the private VPC/subnet and narrowly scoped access controls.
3. Create the instance with reviewed backup, encryption, maintenance, and deletion settings.
4. Wait for the documented ready state.
5. Create the database, least-privilege account, endpoint, and allow-list resources.
6. Store credentials through the approved secret mechanism.
7. Run schema migrations as a separately observable application step.
8. Verify control-plane state, a TLS connection from the intended network, and a minimal read/write transaction.
9. Confirm backups, metrics, alarms, and restore ownership.

Use an application health probe that distinguishes process health from database readiness. Avoid destructive writes in health checks; a simple connection and read query is normally sufficient.

## Change, restore, and delete safely

- Snapshot or confirm a restorable backup before a destructive migration or configuration change.
- Test restore procedures for important environments; the existence of a backup record is not proof of recoverability.
- Apply schema migrations with an explicit forward and rollback strategy appropriate to the migration.
- Inventory endpoints, replicas, accounts, databases, backups, allow-lists, and application consumers before deletion.
- Require resource-specific approval before deleting an instance, database, backup, or final recovery point.
- After cleanup, verify absence and remove stale secret references without exposing their values.
