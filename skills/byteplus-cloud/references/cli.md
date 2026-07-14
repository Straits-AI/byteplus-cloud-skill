# BytePlus CLI

Read this reference before installing, authenticating, or invoking `bp`.

## Install or upgrade safely

Check first:

```bash
command -v bp
bp version
bp --help
```

Use `command -v bp` as the operational source of truth. Do not adopt a binary from
`/tmp`, `/private/tmp`, another operating-system temporary directory, a test fixture,
or a build/staging directory. Those paths are suitable only for isolated installer
tests and must never become the developer's active BytePlus CLI.

Do not assume the documented npm package is available. Query it if npm installation is desired:

```bash
npm view @byteplus/cli version
```

If it is unavailable or the platform package fails, use the bundled release installer. It downloads only from the official `byteplus-sdk/byteplus-cli` GitHub releases and validates the release checksum:

```bash
python3 <skill-dir>/scripts/install_bp.py --dry-run --dest "$HOME/.local/bin"
```

The dry run may resolve `latest`; installation may not. Record and review the
exact version and URLs, then use one of these explicit trust modes:

```bash
# Preferred: digest obtained through an independent trusted channel
python3 <skill-dir>/scripts/install_bp.py \
  --version <reviewed-version> \
  --sha256 <independently-verified-digest> \
  --dest "$HOME/.local/bin"

# Fallback: explicitly accept the official release plus its same-channel checksum
python3 <skill-dir>/scripts/install_bp.py \
  --version <reviewed-version> \
  --trust-official-release \
  --dest "$HOME/.local/bin"
```

For an operational BytePlus task, a missing CLI must end in one of two visible
outcomes:

1. Install it persistently at `$HOME/.local/bin/bp` when the user already authorized
   installing required tooling.
2. Ask the user to approve that exact persistent installation before continuing.

For an explicitly planning-only request or when local installation is forbidden,
do not install; report the missing prerequisite and the exact command the user can
approve later. Do not merely continue with a temporary test binary. Do not use
`sudo`, pipe a remote script into a shell, or replace an existing binary without
`--force` and explicit intent.

The published checksum protects against corruption or an archive/checksum mismatch,
but it is not an independent publisher signature: compromise of the release
channel could replace both. Prefer an archive SHA-256 obtained through a separately
trusted release process. Use `--trust-official-release` only after making that
residual risk visible; the installer records the selected trust mode in JSON.

Example independent pin:

```bash
python3 <skill-dir>/scripts/install_bp.py \
  --version <reviewed-version> \
  --dest "$HOME/.local/bin" \
  --sha256 <independently-verified-digest>
```

The installer does not execute the downloaded binary. After reviewing the installed path, deliberately run:

```bash
"$HOME/.local/bin/bp" version
```

If `$HOME/.local/bin` is not on `PATH`, use that persistent absolute path for the
current workflow and explain the PATH change to the user. Do not silently edit a
shell profile. Once `bp` is available, continue to authentication or the requested
read-only discovery; installation alone is not proof of authentication.

## Choose authentication

Prefer temporary credentials and named profiles.

### Console login for a local developer

BytePlus documents console login as OAuth 2.0 with PKCE. Let the user complete the interactive authorization:

```bash
bp login --profile dev --region ap-southeast-1
```

For a headless server or container:

```bash
bp login --profile dev --region ap-southeast-1 --remote
```

Logging into a non-default profile does not make it current. Prefer explicit fixed flags on every command or deliberately switch with:

```bash
bp configure profile --profile dev
```

Do not parse or copy OAuth cache contents. Use `bp logout --profile dev` when the user asks to clear local console-login state.

### Console OAuth authority

`bp login` authenticates the identity active in the browser. The verified `bp`
v1.0.17 console-login implementation requests the fixed OAuth scope
`Console:All:All` and does not expose a Wrangler-style login scope selector.
Recheck the installed CLI and current official source after an upgrade. That OAuth
scope does not create new IAM authority: an IAM user remains limited by its
policies, while the BytePlus root account remains broadly authorized.

A root result from `GetCallerIdentity` therefore means "valid but privileged," not
"login failed." For local developer use, keep the console-login profile and follow
the privileged-session gates in [security.md](security.md). Do not require the user
to visit IAM before read-only or bounded development work.

### Cloud Identity SSO

Use SSO for enterprise account/role access and for workflows that must interoperate with tools whose CLI credential provider supports SSO but not console-login. Retrieve the current SSO procedure before configuring it. The high-level sequence is:

1. Configure an SSO session.
2. Configure an SSO profile and complete device authorization.
3. Explicitly switch to or name the new profile.
4. Verify identity.

Do not assume `bp configure sso` changes the current profile; the official CLI says it does not.

### Optional hardening without routine console work

Cloud Identity SSO is preferred for an organization that already manages accounts,
permission sets, and roles. Its initial administrator setup may require one-time
console work; do not make it a prerequisite for a solo developer's first BytePlus
task.

When a developer wants least privilege without using the console, first inspect the
live `iam`, `iam20210801`, and `sts` schemas. The verified `bp` v1.0.17 catalog
exposes APIs for users, login profiles, custom policies, project-scoped policy
attachment, roles, and `AssumeRole`. The agent may therefore plan a one-time secure
bootstrap and, after explicit approval of the IAM changes, provision the IAM
resources programmatically instead of asking the developer to click through IAM
console pages.

The preferred restricted-user path still needs one user-controlled browser login
as that IAM user after bootstrap. This is authentication, not manual resource
provisioning. Do not claim that the end-to-end path is zero-touch until it has been
tested for the target account and a trusted helper can accept the initial password
through hidden input. Never pass a login password in `CreateLoginProfile` command
arguments.

Do not create a long-lived access key by default. Normal `CreateAccessKey` output
contains the one-time secret, and direct `sts AssumeRole` output contains temporary
credentials; neither response may enter the agent transcript. The verified v1.0.17
`ramrolearn` profile mode requires source AK/SK and does not directly chain from a
console-login profile. Until a tested credential-isolating helper can capture
temporary credentials and launch child commands without exposing or persisting
them, do not claim that automatic root-OAuth-to-role switching is complete. The
safe default remains console OAuth with effect-based gates; hardened identity
bootstrap is optional.

### Workload and CI credentials

Use an OIDC, assume-role, ECS role, or other documented temporary-credential profile for noninteractive workloads. Bind it to a least-privilege role and short session. Do not turn a local console OAuth cache into a CI secret.

### Long-lived AK/SK

Use only when no temporary path satisfies the product. Ask the user to configure credentials through a protected local or CI secret mechanism. Never request the values in chat, place them in source control, or include them in commands that will be logged.

## Verify the target

Use a read-only identity call with explicit target flags:

```bash
bp sts GetCallerIdentity ---profile dev ---region ap-southeast-1
```

Run the bundled doctor for a redacted view of profile modes and tool availability:

```bash
python3 <skill-dir>/scripts/byteplus_doctor.py \
  --profile dev \
  --region ap-southeast-1 \
  --check-auth \
  --json
```

Do not dump `~/.byteplus/config.json`. The config contains credential and token material even though the file should be mode `0600`.

## Discover instead of guessing

The CLI dynamically exposes its current service and action catalog:

```bash
bp --help
bp ecs --help
bp ecs DescribeInstances --help
```

When another tool needs JSON rather than terminal-formatted help, use the bundled read-only catalog wrapper:

```bash
python3 <skill-dir>/scripts/bp_catalog.py services
python3 <skill-dir>/scripts/bp_catalog.py actions ecs
python3 <skill-dir>/scripts/bp_catalog.py describe ecs RunInstances
python3 <skill-dir>/scripts/bp_catalog.py find endpoint --service ark
```

This wrapper invokes only `--help` and `version`. It cannot infer required fields, enum values, IAM permissions, side effects, regional availability, or pricing that the CLI omits.

Use the spelling and API version shown by the installed CLI. Similar product generations may appear as separate service names. Never substitute a name remembered from Volcano Engine or an older BytePlus release.

The CLI catalog is broad but not universal. A missing service may require a product SDK, S3-compatible tool, Terraform resource, or documented product API. For example, the v1.0.17 catalog does not expose a `tos` service; always recheck the installed version.

## Invoke APIs correctly

General form:

```text
bp <service> <action> [--ApiParameter value ...] [---profile name] [---region region] [---endpoint endpoint]
```

Important distinctions:

- API parameters use two hyphens.
- The only documented fixed invocation flags use three hyphens: `---profile`, `---region`, and `---endpoint`.
- Both `--Param value` and `--Param=value` forms are supported.
- `--body` accepts one JSON object or array for `application/json` requests.
- Do not mix `--body` with flattened API parameters.
- Do not override an endpoint unless the current official documentation requires it.

Prefer a structured JSON body for nested, non-secret inputs. Validate JSON locally and inspect the exact action help before sending it. Do not interpolate untrusted project text into a shell command; pass arguments as an array when invoking from code.

## Debug safely

Use normal sanitized errors first. When current CLI docs recommend debug logging, enable it for one command only and review the generated output before sharing it. Debug logs can include action inputs, profile metadata, endpoints, and request context.

Never publish:

- access keys, secret keys, or session tokens;
- OAuth or SSO refresh/access tokens;
- authorization headers;
- secret-bearing request bodies;
- the complete local profile file;
- signed URLs whose query string grants access.

## Apply the imperative-operation protocol

1. Run a Describe/Get/List action first.
2. Confirm the installed action schema and official semantics.
3. Show the exact target and effects.
4. Execute once.
5. Capture request ID and structured result.
6. Poll documented asynchronous status with a timeout.
7. Read back and compare expected state.
8. Record non-secret resource IDs and cleanup steps.

Do not invent a universal `bp plan`, dry-run, transaction, or rollback command; the generic CLI does not provide one.
