# BytePlus Edge Functions

Use `@byteplus/nest` for Edge Functions and Edge Functions Pages. It is a product-specific application lifecycle CLI, unlike the generic `bp` API dispatcher.

## Confirm and pin the CLI

Check current registry metadata before downloading executable tooling:

```bash
npm view @byteplus/nest version
```

Inform the user before installing a new package. Prefer a project-local, verified version for reproducibility:

```bash
npm install --save-dev @byteplus/nest@<verified-version>
npx nest --version
npx nest --help
```

Retrieve subcommand help before use. The v1.3.2 live command surface included project initialization, start/debug/build, deployment, functions, Pages, domains, cron, environment variables, KV, versions, release tickets, canary, rollback, configuration, and MCP.

Do not claim a `logs` command unless live help adds one. `--verbose` is CLI verbosity, not production log tailing. `nest start` creates a local HTTP proxy connected to BytePlus's remote WSS debugger; do not describe it as a fully offline emulator.

## Use the lifecycle

1. Inspect an existing `nest.json` and project source before initialization.
2. Initialize only in an intended empty/new directory.
3. Run the current start/debug/build workflow and application tests.
4. Inspect the target function, canary configuration, and deployment history.
5. Deploy to canary first when the application and account support it.
6. Verify the bound domain/trigger and live behavior.
7. Record the deployed function ID, version, and release ticket.
8. Retrieve current rollback syntax and preserve the exact last-known-good version.

Current deploy and rollback behavior targets the full/production environment unless `--canary` is supplied. Treat both operations as production mutations.

## Treat credentials as a separate boundary

Current Edge Functions documentation requires an Access Key ID and Secret Access Key in project or global `nest` configuration for function create, pull, and deploy operations. `nest start` is documented without that requirement. The documentation does not describe transparent reuse of `bp login` OAuth profiles.

Apply these rules:

- Never place `cloud.access_key` or `cloud.secret_key` in a committed `nest.json`.
- Never ask the user to paste credentials into chat or put them in a `nest config set` process argument.
- Prefer a least-privilege dedicated identity when no temporary credential path is documented.
- Ask the developer to configure the credential outside the agent workflow.
- Prefer global `~/.nest.json` over a project file only when the user accepts machine-wide scope; restrict its permissions.
- Inspect Git status and ignore rules before and after any configuration change.
- Never print effective config while credentials may be present.

Stop if the only available path would expose a permanent secret to the agent or repository.

## Use the official MCP narrowly

The bundled [MCP template](../assets/mcp.edge-functions.json) pins the version tested with this skill. Copy it only after the user opts into the package download, and re-check current registry metadata before changing the pin.

A package version pin is not an integrity pin. For higher-assurance environments,
install the reviewed package through a committed lockfile and configure the MCP
client to run that project-local installation. Keep the bundled `npx` template an
explicit opt-in because it relies on the npm registry and package-manager cache at
startup.

BytePlus's official integration guide documents five tools: `init_project`, `add_function`, `pull_function`, `deploy_function`, and `start_function`. A live `tools/list` check against `@byteplus/nest` v1.3.2 also exposed `deploy_pages`. Treat live `tools/list` as the capability contract for the installed server and do not infer any other tools.

The MCP does not expose the whole BytePlus account. Use direct current CLI help for rollback, versions, tickets, domains, canary, KV, cron, environment variables, and other unlisted commands. Keep the function project directory inside the agent's workspace context.

## Verify deployment

- Confirm the function or Pages ID and deployed version.
- Confirm the intended production/canary target.
- Exercise the actual domain and forwarding rule.
- Test failure and fallback behavior.
- Inspect release tickets/history and the current product metrics surface.
- Do not claim runtime log tailing through `nest`; current v1.3.2 help has no such command.
- Do not treat CDN request-log products as proof of Edge Functions `console.log` visibility.

## Official sources

- [CLI installation](https://docs.byteplus.com/docs/byteplus-cdn/get-started-with-edge-function-cli-en)
- [CLI command list](https://docs.byteplus.com/api/docs/byteplus-cdn/edge-funcition-cli-command-ref-en)
- [`nest start`](https://docs.byteplus.com/en/docs/byteplus-cdn/cli-ref-nest-start-en)
- [`nest deploy`](https://docs.byteplus.com/api/docs/byteplus-cdn/cli-ref-nest-deploy-en)
- [`nest versions`](https://docs.byteplus.com/api/docs/byteplus-cdn/cli-ref-nest-version-en)
- [`nest rollback`](https://docs.byteplus.com/api/docs/byteplus-cdn/cli-ref-nest-rollback-en)
- [Credential setup](https://docs.byteplus.com/en/docs/byteplus-cdn/edge-functions-cli-login-en)
- [MCP integration](https://docs.byteplus.com/en/docs/byteplus-cdn/integrate-mcp-server-en)
- [Release notes](https://docs.byteplus.com/en/docs/byteplus-cdn/edge-functions-release-notes-en)
- [Function metrics](https://docs.byteplus.com/en/docs/byteplus-cdn/docs-View-Function-Metrics)
