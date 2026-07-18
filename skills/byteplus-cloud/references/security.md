# Security and approval gates

Apply these controls to every remote BytePlus operation.

## Classify the full effect

Do not classify risk from the action name alone. Inspect parameters, target environment, dependencies, replacement behavior, and product defaults.

| Class | Examples | Default behavior |
|---|---|---|
| Read-only | List, Describe, Get, identity, status, metrics | Run when in scope; redact output |
| Local reversible | Code/config/IaC edits, validation, non-secret build | Run within the requested workspace |
| Ordinary mutation | Explicitly requested private, bounded, pay-as-you-go development resource with cleanup ownership | Show the target and effects; proceed within the user's stated authorization |
| High impact | Production deploy, public endpoint, IAM/networking change, prepaid commitment, or expensive/unbounded compute, database, or GPU capacity | Require explicit approval of the exact target and effects unless that exact plan was already approved |
| Destructive | Delete, destroy, purge, data overwrite, key rotation, backup removal, destructive replacement | Require resource-specific approval and a recovery check |
| Account critical | Create unrestricted IAM, disable audit/security controls, weaken root-account security, or close the account | Deny by default; require exceptional explicit scope and independent safeguards |

## Handle privileged OAuth without blocking local development

Caller privilege modifies risk; it does not replace the operation classification
above.

When `GetCallerIdentity` reports the BytePlus root account:

- Treat the login as successful. Console OAuth uses temporary credentials, but
  temporary credentials can still have root authority.
- Show one concise warning for the current profile, masked account, and region. Do
  not repeat it unless the target changes.
- Continue requested read-only operations immediately.
- For a bounded, private development mutation, disclose the exact resources, cost
  class or retrieved estimate, security posture, verification, and cleanup.
  Proceed under the user's existing authorization; do not add another confirmation
  solely because the caller is root.
- Keep the normal exact-plan approval gates for production, public exposure,
  IAM/networking, prepaid or unbounded cost, replacement, deletion, and other
  high-impact effects.
- Do not treat OAuth consent as blanket authorization for future cloud mutations.
- Do not tell the developer that they logged in incorrectly, and do not force
  IAM-console setup solely because the caller is root.

Offer least-privilege hardening once, preferably before production work or in the
final handoff. Do not interrupt each command with the same recommendation.

An update action can be destructive. Examples include making a bucket public, opening a security group, shrinking or replacing a database, changing a route, rotating credentials, or altering a role trust policy.

## Bind the target

Before mutation, display and verify:

- profile and authentication mode;
- non-secret caller identity/account;
- region;
- environment and project;
- resource IDs;
- whether the target is production;
- current state relevant to the change.

Use explicit profile and region flags. Stop if target resolution relies on an ambiguous ambient default.

## Protect credentials and secrets

Never:

- ask the user to paste AK/SK, session tokens, OAuth codes, refresh tokens, passwords, or private keys into chat;
- print or read entire BytePlus/nest credential files;
- commit secrets, `.tfvars` with secrets, state, or secret-bearing manifests;
- put secrets into shell history, process arguments, debug logs, issue reports, or deployment summaries;
- expose signed URLs or authorization headers;
- copy console-login tokens into Terraform or CI.

Prefer browser/device login, short-lived role credentials, OIDC workload identity, protected secret stores, and stdin/file-descriptor handoff supported by the target tool.

Treat a veFaaS `GenWebshellEndpoint` response as a secret-bearing signed URL. A
credential-isolating client must capture it in memory, connect without printing or
persisting it, emit only sanitized status/evidence, close promptly, and discard it.
Never put the ticketed WSS endpoint in a run ledger or deployment report.

Apply the same rule to AgentKit tool authorizers and session endpoints. Current
CLI JSON output may include the generated API key directly, and session endpoints
may carry authorization in their query strings even when a field filter was
requested. Do not print raw `tools show`, `session show`, or `session list` output;
capture and redact it before emitting safe fields.

Redact fields whose names contain terms such as `access_key`, `secret`, `session_token`, `token`, `password`, `passphrase`, `credential`, `authorization`, `cookie`, `private_key`, `api_key`, `signature`, or `signed_url`. Redact complete authorization/cookie headers and complete PEM private-key blocks, not only the first whitespace-delimited value.

## Keep least privilege

- Use separate observer and deployer roles when practical.
- Limit account, project, region, services, actions, and resource patterns.
- Use session policies to narrow temporary credentials where supported.
- Do not add broad wildcards to diagnose a denial.
- Review IAM trust and pass-role effects, not only attached policy text.
- Retest after reducing permissions.

A service-linked role is still an IAM mutation. Read the exact documented role,
service principal, managed policy, and trust relationship before creation; require
approval for that specific role. Prefer the current `CreateServiceLinkedRole` API
when the product's service name is documented and live help confirms it. Do not
grant `IAMFullAccess`, create a generic broad role, or guess
`ServiceRoleFor<Service>` merely to make an opaque create error disappear. Preserve
shared service-linked roles during workload cleanup unless their revocation was
separately approved and dependency-checked.

## Default to private and recoverable

- Keep storage, databases, compute, and load balancers private unless public access is necessary and approved.
- Avoid `0.0.0.0/0` and `::/0` ingress; constrain protocol, port, and source.
- Enable encryption, backup, deletion protection, and audit/monitoring features appropriate to the product and environment.
- Prefer staging/canary and bounded rollout.
- Preserve a tested rollback version or recovery path.

Retrieve current product semantics before claiming that a specific flag enables these controls.

## Control cost and quota

Before creating or resizing billable resources:

- retrieve current pricing and billing mode;
- confirm instance/specification, count, storage, bandwidth, retention, and region;
- check quota and capacity;
- avoid prepaid commitments unless explicitly requested;
- disclose resources that continue billing while stopped;
- include cleanup ownership and expiry for experiments.

Do not present an estimate as a quote. Ask for a budget decision when multiple architectures differ materially in cost.

## Preserve auditability

Record sanitized:

- approved plan and target;
- command/action or Terraform plan identity;
- request IDs and timestamps;
- changed resource IDs;
- verification results;
- rollback/cleanup instructions.

Do not record secret inputs or complete credential-bearing responses.
