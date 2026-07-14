# Current sources and retrieval order

Use current primary sources. Bundled references explain workflow and known gaps; they are not authoritative for volatile facts.

This skill uses on-demand retrieval rather than maintaining a mirror of BytePlus
documentation. Do not silently crawl or vendor the documentation into a project.
When durable evidence is needed, record the canonical URL, retrieval date, tool or
SDK version, and the narrow non-secret fact used; retrieve the source again before
the next consequential operation.

## Resolution order

1. Inspect the installed tool's live schema or help for syntax and currently exposed capability.
2. Read the current official BytePlus product documentation for semantics, prerequisites, regions, limits, quotas, billing, and side effects.
3. Inspect the current Terraform Registry schema or installed SDK types for machine-readable inputs and outputs.
4. Check official release notes and repository releases for recent changes or regressions.
5. Use these bundled references only as routing guidance.

When sources disagree, stop before mutation and resolve the discrepancy. A CLI action existing does not prove that it is available in the target region or account.

## Official entry points

- BytePlus documentation: <https://docs.byteplus.com/en/>
- BytePlus CLI repository: <https://github.com/byteplus-sdk/byteplus-cli>
- BytePlus CLI releases: <https://github.com/byteplus-sdk/byteplus-cli/releases>
- BytePlus CLI usage: <https://github.com/byteplus-sdk/byteplus-cli/blob/main/docs/4-Usage.md>
- BytePlus CLI authentication: <https://github.com/byteplus-sdk/byteplus-cli/blob/main/docs/2-Authentication.md>
- BytePlus CLI configuration: <https://github.com/byteplus-sdk/byteplus-cli/blob/main/docs/3-Configuration.md>
- BytePlus CLI console-login implementation: <https://github.com/byteplus-sdk/byteplus-cli/blob/main/cmd/consolelogin_login.go>
- BytePlus IAM API overview: <https://docs.byteplus.com/en/docs/byteplus-platform/reference-overview-5>
- BytePlus IAM policy syntax: <https://docs.byteplus.com/en/docs/byteplus-platform/reference-policy>
- BytePlus IAM CreateLoginProfile API: <https://docs.byteplus.com/en/docs/byteplus-platform/reference-createloginprofile>
- BytePlus STS AssumeRole API: <https://docs.byteplus.com/en/docs/byteplus-platform/reference-assumerole>
- BytePlus role management: <https://docs.byteplus.com/en/docs/byteplus-platform/docs-managing-roles>
- BytePlus project permission management: <https://docs.byteplus.com/en/docs/resourcemanagement/Project_Permission_Management>
- BytePlus Cloud Control Terraform provider: <https://github.com/byteplus-sdk/terraform-provider-bytepluscc>
- Terraform Registry provider: <https://registry.terraform.io/providers/byteplus-sdk/bytepluscc/latest/docs>
- Function Service documentation: <https://docs.byteplus.com/en/docs/faas/>
- Function Service API list: <https://docs.byteplus.com/en/docs/faas/API_list>
- Function Service pay-as-you-go billing: <https://docs.byteplus.com/en/docs/faas/Pay-as-you-go>
- veFaaS Cloud Sandbox: <https://docs.byteplus.com/en/docs/faas/Cloud_sandbox>
- veFaaS GenWebshellEndpoint API: <https://docs.byteplus.com/en/docs/faas/GenWebshellEndpoint>
- Edge Functions CLI overview: <https://docs.byteplus.com/en/docs/byteplus-cdn/edge-function-cli-overview-en>
- Edge Functions command list: <https://docs.byteplus.com/en/docs/byteplus-cdn/edge-funcition-cli-command-ref-en>
- Edge Functions MCP overview: <https://docs.byteplus.com/en/docs/byteplus-cdn/edge-functions-mcp-server-overview-en>
- Edge Functions MCP guide: <https://docs.byteplus.com/en/docs/byteplus-cdn/integrate-mcp-server-en>
- Edge Functions CLI releases: <https://docs.byteplus.com/en/docs/byteplus-cdn/edge-functions-release-notes-en>
- TOS API overview: <https://docs.byteplus.com/en/docs/tos/reference-api-overview>
- TOS SDK overview: <https://docs.byteplus.com/en/docs/tos/SDK-overview>
- TOS S3 compatibility: <https://docs.byteplus.com/en/docs/tos/docs-compatibility-with-amazon-s3>
- ModelArk documentation: <https://docs.byteplus.com/en/docs/ModelArk/>
- ModelArk model list: <https://docs.byteplus.com/en/docs/ModelArk/1330310>
- ModelArk Activation Management: <https://docs.byteplus.com/en/docs/modelark/1159200>
- ModelArk Image generation API: <https://docs.byteplus.com/en/docs/ModelArk/1541523>
- ModelArk Video generation API: <https://docs.byteplus.com/en/docs/ModelArk/1520757>
- Seed Speech documentation: <https://docs.byteplus.com/en/docs/byteplusvoice>
- Seed Speech Console Guide: <https://docs.byteplus.com/en/docs/byteplusvoice/Speech_Console_Guide>
- Seed Speech HTTP TTS API: <https://docs.byteplus.com/en/docs/byteplusvoice/unidirectional_tts_http>
- Seed Speech WebSocket TTS API: <https://docs.byteplus.com/en/docs/byteplusvoice/streaming_tts>
- RDS for MySQL documentation: <https://docs.byteplus.com/en/docs/RDS_for_MySQL/about_rds_for_mysql>
- RDS for PostgreSQL documentation: <https://docs.byteplus.com/en/docs/RDS_for_PG/>
- RDS for SQL Server documentation: <https://docs.byteplus.com/en/docs/RDS_for_SQLServer/>

## Freshness checklist

Before using an exact command or schema:

- record the installed tool/provider/SDK version;
- retrieve the relevant help or schema from that version;
- check its latest official release date and release notes;
- retrieve the product page's current update date when available;
- confirm region and account availability;
- avoid copying numeric limits or pricing into project documentation unless the user needs them and the source is cited.

## Known source caveats

- The CLI repository documents an npm installer, but registry availability has been inconsistent. Probe it rather than assuming it works; prefer the checksum-verifying release installer bundled with this skill.
- Cloud Control covers only supported resource types. Its repository explicitly directs users to request missing resources.
- BytePlus and Volcano Engine use related technology but different international/domestic control planes. Never reuse Volcano Engine endpoints, credentials, regions, Terraform resources, or MCP servers without explicit BytePlus compatibility documentation.
- BytePlus does not currently publish a general documentation MCP comparable to Cloudflare Docs MCP. Use official web retrieval plus live tool/provider schemas.
