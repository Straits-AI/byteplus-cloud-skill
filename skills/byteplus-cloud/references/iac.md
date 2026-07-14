# BytePlus infrastructure as code

Use the official BytePlus Cloud Control provider for supported persistent infrastructure. Treat its resource registry as a capability boundary, not as proof of complete BytePlus coverage.

## Select Terraform when appropriate

Prefer Terraform or OpenTofu for:

- multiple dependent resources;
- persistent development, staging, or production environments;
- reviewable plans and destructive-change detection;
- repeatable deployment and CI/CD;
- drift detection and import of existing resources.

Prefer `bp` or a product SDK for diagnostics, operational actions, data-plane operations, or resources absent from Cloud Control.

## Retrieve the current provider contract

Use the official source `byteplus-sdk/bytepluscc`. Before authoring resources:

1. Check the current Terraform Registry release and provider requirements.
2. Pin a compatible version; do not copy an old example version from a README.
3. Read the exact resource/data-source page.
4. Run `terraform providers schema -json` after initialization when a machine-readable schema is useful.
5. Check import syntax and whether important fields force replacement.

Prefer the installed provider schema over generated prose when they disagree. The v0.0.45 generated assume-role documentation and implementation diverged, and some nested set/list resources warn that incomplete nested values can cause unexpected differences. Do not copy an assume-role block from an example or run an unattended apply without inspecting the installed schema and plan.

The provider currently requires a region and either static credentials or a profile. Keep both as variables or environment configuration, never literals committed to source.

## Respect the authentication gap

Do not assume every `bp` profile mode works in the Cloud Control provider.

Verified baseline on 13 July 2026: BytePlus Cloud Control provider `v0.0.45` pins BytePlus Go SDK `v1.0.51`. That SDK's CLI credential provider accepts AK and SSO profile modes but rejects `console-login`, OIDC, RAM-role, and ECS-role profile modes. Therefore a profile created by `bp login` OAuth does not work with this released Terraform baseline. The newer SDK used by `bp` supports more modes, but the provider has not inherited them until its pinned dependency changes.

Before planning infrastructure:

1. Use the doctor to identify the profile mode without exposing credentials.
2. If the mode is SSO, verify a read-only provider operation.
3. If the mode is console-login, do not extract its cached STS credentials. Use a documented SSO/workload profile, or fall back to supported `bp` operations where appropriate.
4. Recheck current provider version and pinned SDK behavior because this limitation may change after `v0.0.45`.

## Configure without secrets

Use variables or environment configuration for target selection:

```hcl
terraform {
  required_providers {
    bytepluscc = {
      source  = "byteplus-sdk/bytepluscc"
      version = "<currently-verified-version>"
    }
  }
}

variable "byteplus_profile" {
  type = string
}

variable "byteplus_region" {
  type = string
}

provider "bytepluscc" {
  profile = var.byteplus_profile
  region  = var.byteplus_region
}
```

Replace the version placeholder before running `terraform init`. Do not commit profile files, `.tfvars` containing secrets, local state, plan files containing sensitive values, or credential exports.

## Apply a reviewable lifecycle

```bash
terraform fmt -check -recursive
terraform init
terraform validate
terraform plan -out=byteplus.tfplan
terraform show byteplus.tfplan
terraform apply byteplus.tfplan
```

Adapt commands to the repository and backend. Before apply:

- confirm workspace/backend/account/region;
- inspect all `-/+` replacements and destroys;
- check public IPs, ingress CIDRs, IAM policies, encryption, backups, and deletion protection;
- confirm sizes, billing types, quantities, and region availability from current docs;
- ensure the saved plan has not gone stale.

Delete the local plan file after use if it may contain sensitive values.

## Manage state carefully

- Use the repository's existing remote backend and locking when present.
- Never edit state manually for convenience.
- Back up state before recovery work.
- Import existing resources instead of recreating them when safe.
- Never run `terraform destroy`, remove state entries, force-unlock, or migrate a backend without explicit authorization and a resource-specific review.
- Treat rollback as a new reviewed convergence plan; reverting Git alone does not revert remote infrastructure.

## Handle unsupported resources

If a resource is absent from the current provider schema:

1. Check the current `bp` action catalog.
2. Check the official product SDK/API.
3. Keep imperative operations in an idempotent deployment script with read-before-write and verification.
4. Record ownership in the project manifest so Terraform does not claim unmanaged state.

Do not use the deprecated legacy BytePlus Terraform provider for a missing resource without the user's explicit acceptance of its maintenance and migration risk.

## Authentication evidence for the verified baseline

- [BytePlusCC v0.0.45 provider dependency](https://github.com/byteplus-sdk/terraform-provider-bytepluscc/blob/v0.0.45/go.mod)
- [BytePlus Go SDK v1.0.51 CLI profile provider](https://github.com/byteplus-sdk/byteplus-go-sdk-v2/blob/v1.0.51/byteplus/credentials/clicreds/cli_provider.go)
- [BytePlus Go SDK v1.0.68 expanded profile support](https://github.com/byteplus-sdk/byteplus-go-sdk-v2/blob/v1.0.68/byteplus/credentials/clicreds/cli_provider.go)
