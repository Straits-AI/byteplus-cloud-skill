# Beyond the Portal: What the Next Generation of Cloud Providers Must Deliver

*A practical requirements framework for cloud providers in Malaysia and beyond*

The next cloud customer may not be a person clicking through a web console. It may be a coding agent acting for a developer: inspecting an application, choosing an architecture, provisioning infrastructure, deploying the code, reading logs, fixing a failure, and cleaning up the resources afterward.

That shift changes what it means to be a modern cloud provider.

Data centres, local latency, data residency, reliable compute, and responsive human support still matter. They are real advantages, especially in Malaysia. But they are no longer enough. A cloud must also be operable as software: programmable, discoverable, governable, observable, and reproducible.

This is not merely an AI trend. Coding agents expose a distinction that has existed for years:

> Is the provider's control plane a complete product interface, or is the customer portal only a window into an operator-managed hosting business?

The next generation of cloud providers will be defined by how convincingly they answer that question.

## Agents reveal the quality of the control plane

A modern cloud normally follows this model:

```text
Documented API as the source of truth
    → CLI, SDK, console, and infrastructure as code
    → CI/CD, integrations, and agent tools
    → governed, observable operations
```

A traditional hosting model is often closer to:

```text
Internal operations system
    → customer portal exposes selected functions
    → unsupported changes become tickets or quotations
    → staff complete the operation manually
```

The second model can still provide dependable infrastructure and valuable managed service. But it cannot support fast, ephemeral, automated workflows well. A developer cannot reliably ask an agent to create a staging environment, test a branch, diagnose the deployment, and destroy everything afterward if some of those steps require a form, an invoice, or a support conversation.

The leading platforms are already moving beyond API access alone. [Cloudflare's skills repository](https://github.com/cloudflare/skills) combines product knowledge, deployment workflows, and remote MCP services for APIs, documentation, builds, bindings, and observability. The [Agent Toolkit for AWS](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/what-is-agent-toolkit.html) combines current documentation, tested skills, authenticated API execution, IAM controls, metrics, and CloudTrail auditability. [Azure MCP Server](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/overview) connects agents to Azure resources using Entra ID and works alongside the Azure CLI, Azure Developer CLI, and reusable deployment and diagnostics skills. The [Alibaba Cloud Agent Skills Portal](https://www.alibabacloud.com/help/en/skillsportal/learn-about-the-alibaba-cloud-agent-skills-portal) publishes tested skills for natural-language resource management, cross-product orchestration, and solution deployment.

These products are not important because they add chat to a cloud console. They are important because they make an already programmable cloud understandable and usable by agents.

## A maturity model for cloud providers

The following proposed six-level model is a practical diagnostic, not an industry standard. It describes the customer-facing operating model, not the quality of the underlying hardware or engineering team. A provider may also sit at different levels for different products.

| Level | Operating model | Customer experience |
|---|---|---|
| 0 — Manual host | Staff provision and change infrastructure | Orders, email, calls, and tickets |
| 1 — Hosting portal | Basic server and billing operations are self-service | Reboot, reinstall, renew, and upgrade through a client area |
| 2 — Self-service IaaS | Compute, storage, and networking are exposed in a console | Customers operate resources through a web UI |
| 3 — Programmable cloud | A public API, CLI, SDK, and scoped credentials cover routine operations | Infrastructure can be scripted and integrated |
| 4 — Cloud-native platform | Declarative state, events, observability, autoscaling, and a developer ecosystem are first-class | Environments are reproducible and operated continuously |
| 5 — Agent-operable cloud | Current knowledge, agent skills, safe execution, policy, verification, and recorded action origins are integrated | Agents can complete end-to-end workflows under human control |

An MCP server does not move a provider directly from Level 2 to Level 5. MCP is an interface, not a control plane. If routine actions are unavailable through stable APIs, an MCP can only wrap the limitations—or resort to brittle browser automation.

## The twelve requirements of a next-generation cloud

### 1. A complete, public, API-first control plane

Every routine action available to a customer should have a documented, versioned API. The console should consume the same public resource model rather than expose privileged operations that automation cannot reach.

That API needs more than CRUD endpoints. It needs:

- predictable asynchronous operation states;
- idempotency for safe retries;
- structured errors and request identifiers;
- consistent pagination and filtering;
- quotas and regional availability;
- lifecycle events or webhooks;
- deprecation and compatibility policies.

Support should help with exceptions. It should not be a required step in the normal control plane.

### 2. A first-class CLI and SDK experience

For a provider serving developers, a CLI should be treated as a primary product interface rather than a secondary alternative to the web UI. It is the simplest reproducible interface for developers, CI/CD systems, and coding agents.

A capable cloud CLI should support interactive login, service and action discovery, machine-readable JSON output, stable exit codes, profiles and regions, schema-aware help, and safe handling of complex request bodies. A command executed by an agent should be understandable and repeatable by a human.

Official SDKs should use the same authentication chain and provide consistent errors, retries, pagination, and long-running-operation support.

### 3. Declarative infrastructure and state

The platform should support Terraform or OpenTofu, Pulumi, or an equivalent declarative model with:

- plan, diff, apply, import, and destroy;
- documented resource schemas;
- dependency management;
- drift detection;
- sensitive-property handling;
- predictable update and replacement semantics.

This turns infrastructure changes into reviewable code. Without it, cloud state becomes a collection of portal decisions and undocumented operator actions.

### 4. Identity for humans, workloads, and agents

Username-and-password access to a billing account is not an automation strategy.

A next-generation provider needs browser or device login for developers, enterprise SSO, service identities, role assumption, short-lived credentials, OIDC workload federation, and resource- or project-scoped permissions. Credentials must be revocable and auditable without exposing long-lived secrets to an agent.

Agent activity should also carry provenance. AWS, for example, adds MCP-specific context keys to API requests and records the resulting calls in CloudTrail, allowing policies and audits to distinguish agent-mediated actions from direct ones. That is a useful benchmark for the industry.

### 5. Current, machine-readable documentation

Agents are especially sensitive to stale documentation. They need authoritative sources for action names, parameters, supported regions, quotas, limits, pricing, and deprecations.

Providers should publish OpenAPI or equivalent schemas, JSON Schema where appropriate, changelogs, error catalogues, complete code examples, and structured metadata for service availability. Documentation search or a read-only documentation MCP can make that information retrievable on demand.

The goal is not to copy the entire documentation set into every agent skill. Skills should contain stable procedures and navigation knowledge, then retrieve current product facts when needed.

### 6. An agent-native knowledge layer

Raw API access is broad but not intelligent. An agent still needs provider-maintained operational knowledge: which product to choose, which resources depend on each other, how to deploy an application, and how to verify that the result works. This is the “agent-native knowledge layer.”

Provider-maintained Agent Skills can supply:

- product-selection guidance;
- tested deployment procedures;
- configuration and security conventions;
- troubleshooting playbooks;
- scripts and templates;
- current documentation entry points.

MCP servers can add structured access to documentation, resource APIs, builds, logs, and metrics. Both should reveal details progressively: load the knowledge and tools relevant to the current task instead of sending thousands of API definitions to the agent at once.

### 7. Plans, approvals, policy, and cost guardrails

Natural language should not mean unreviewed infrastructure changes.

The platform should distinguish harmless reads from billable creation, network and IAM changes, and destructive operations. It should support previews, resource-specific approval, parameter constraints, project and region boundaries, spend and quota policies, and explicit denial of sensitive account operations.

The right experience is not “the agent can do everything.” It is “the agent can do everything it has been deliberately authorized to do, with the right review at the right risk level.”

### 8. Observability and an auditable operation history

Provisioning is only the beginning. An agent must be able to determine whether a deployment actually works.

That requires the status of create, update, and delete requests, plus resource health, logs, metrics, traces, cost data, deployment history, and correlation identifiers. Every mutation should leave an audit record containing the identity, origin, inputs, affected resources, outcome, and time.

For long-running operations, the agent needs a stable operation ID and a supported way to poll or subscribe to completion. For failures, it needs structured errors rather than a generic portal notification.

### 9. A complete application lifecycle

Developers do not merely “create a virtual machine.” They deploy applications.

A competitive provider should make it possible to:

1. inspect the application and select an architecture;
2. provision compute, storage, networking, identity, and data services;
3. configure secrets and application bindings;
4. deploy the code;
5. verify health and connectivity;
6. read logs and diagnose failures;
7. roll back safely;
8. record the resulting state;
9. clean up all resources.

If these steps require unrelated portals, inconsistent credentials, and support intervention, the provider has infrastructure products but not yet a coherent developer platform.

### 10. Open standards and portability

Providers do not need to imitate a hyperscaler, but they should meet developers where the ecosystem already exists.

Useful standards include OAuth and OIDC for identity, OpenAPI for service contracts, Terraform or OpenTofu for state, Kubernetes for container orchestration, S3 compatibility for object storage where appropriate, and MCP and Agent Skills for agent integration.

Portability also requires a credible exit path: exportable infrastructure and application state, documented data migration, backups that can be restored elsewhere, predictable egress charges, and supported ways to remove resources and credentials cleanly. Standards reduce the cost of adoption and allow a smaller provider to benefit from mature tools without inventing an entire ecosystem alone.

### 11. Developer-grade onboarding and economics

A developer should be able to understand regions, service availability, quotas, and pricing before speaking to sales. They should be able to create a sandbox, authenticate, make a harmless read call, and deploy a small workload quickly.

Transparent prices, predictable billing units, test accounts, useful free allowances, fast quota feedback, and actionable errors all matter. A quotation remains appropriate for a bespoke managed deployment; it should not be the default gateway to ordinary cloud experimentation.

### 12. Continuous conformance testing

An agent integration is only as good as the workflows it has actually completed.

Providers should maintain automated end-to-end tests for representative tasks: create and delete a network, deploy a function, provision a VM, assume a role, upload an object, call an AI model, retrieve logs, roll back a deployment, and verify that cleanup leaves no billable resources.

These tests should run when APIs, CLIs, schemas, regions, or skills change. “Theoretically supported” is not the same as a dependable developer experience.

## A working example: the BytePlus Cloud Skill

We built the open-source [BytePlus Cloud Skill](https://github.com/Straits-AI/byteplus-cloud-skill) to test this framework against a real regional cloud and real coding agents.

It gives Codex, Claude Code, Cursor, and other compatible agents a retrieval-first operating layer over BytePlus's official CLI, APIs, Cloud Control provider, SDKs, and product tools.

The project covers resource planning, OAuth-based CLI use, infrastructure routing, deployment procedures, verification, approval boundaries, rollback, cleanup, and current-document retrieval.

It is deliberately published as a public preview rather than a universal-support claim.

The [validation matrix](https://github.com/Straits-AI/byteplus-cloud-skill/blob/main/docs/validation-matrix.md) separates live end-to-end evidence from partial and guidance-only coverage.

Validated paths include CLI and OAuth bootstrap, an ECS application deployment with cleanup, a veFaaS event function, Cloud Sandbox, ModelArk text, image and video generation, and Seed Speech TTS.

Known gaps remain visible, including a ready managed custom AgentKit runtime, a
public HTTP/API Gateway path, Edge Functions, Terraform stacks, TOS, VKE, managed
databases, and broad observability acceptance. A minimal AgentKit All-in-one
(`CodeEnv`) sandbox has been created, invoked, and cleaned up through the official
API/CLI path. A deterministic custom A2A application has passed local Python and
official `linux/amd64` AgentKit-container health, discovery, and protocol
invocation. Its official Container Registry build/push also succeeded, but two
managed creates stopped at `Error`, version 0, without an endpoint or key; the
exact runtimes and registry hierarchy were then removed and zero inventories
verified.

The repository is Apache-2.0 licensed, accepts contributions, and runs public [continuous integration](https://github.com/Straits-AI/byteplus-cloud-skill/actions/workflows/ci.yml) across its offline tests and structural checks.

Developers can inspect the source and install the skill with:

```bash
npx skills add Straits-AI/byteplus-cloud-skill \
  --skill byteplus-cloud \
  --global
```

This work demonstrates the central argument of this article. A skill can make a programmable but fragmented cloud much easier for agents to use, but it cannot manufacture missing APIs, permissions, entitlements, or product-level automation.

## What the Malaysian market reveals

Malaysia's providers have meaningful advantages: local data residency, Ringgit billing, low latency, familiar support, and infrastructure designed for local regulatory and business needs. Those strengths should be preserved.

The following are illustrative cases selected because their public materials expose different Malaysian cloud and hosting models. They are not a complete market census. In these examples, the public developer surface tells a more traditional story.

The clearest example is IPServerOne NovaCloud. IPServerOne documents [NovaCloud as an OpenStack-based service](https://www.ipserverone.info/knowledge-base/how-to-get-started-with-novacloud/), yet its own [Terraform FAQ](https://www.ipserverone.info/faq/faq-terraform-for-novacloud/) states that Terraform is unsupported because its API is not publicly accessible. This is a useful illustration of a broader pattern: a modern infrastructure substrate can still be delivered through a traditional customer interface.

[Exabytes Vision Cloud](https://www.exabytes.my/enterprise/evc) presents substantial enterprise capabilities—virtual-machine lifecycle management, monitoring, networking, disaster recovery, data sovereignty, and a centralized console. Its public product journey, however, emphasizes a fully managed platform, local technical support, and “Contact Cloud Experts.” That may be the right commercial model for many enterprise customers, but it is not the same as a publicly documented developer control plane. This observation does not prove that private or internal APIs do not exist; it describes the interface offered in the inspected public material.

[ServerFreak's cloud-server upgrade guide](https://help.serverfreak.com/en/article/how-to-upgrade-cloud-server-resources-1c7zbcb/) shows a portal-and-billing workflow: choose resource upgrades in the client area, pay the prorated charge, and reboot the server to apply them. This is a legitimate VPS-hosting experience. It is simply a different product category from an API-driven, composable cloud.

The criticism should therefore be precise. The problem is not that Malaysian providers lack capable infrastructure or good people. Nor should the absence of public developer documentation be treated as proof that no internal automation exists.

The gap is a public developer contract: documented and versioned resource APIs, official tooling, scoped credentials, infrastructure as code, machine-readable documentation, auditable operations, and workflows that do not fall back to tickets for routine changes. An AI assistant can improve the portal experience, but it cannot substitute for that foundation.

## A minimum viable next-generation cloud

For a provider beginning this transformation, the first milestone does not require a vast catalogue of AI features. It requires a solid programmable foundation.

A credible initial release should include:

- public APIs covering the routine lifecycle of its core compute, storage, and network products;
- a supported CLI with JSON input and output;
- developer login plus scoped, short-lived workload credentials;
- a Terraform or OpenTofu provider with plan and import support;
- structured documentation, schemas, errors, quotas, and changelogs;
- operation status, audit logs, resource health, and cost visibility;
- tested Agent Skills for provisioning, deploying, diagnosing, and cleaning up;
- an MCP layer for current documentation and constrained cloud operations;
- risk-based approval and cost controls;
- end-to-end conformance tests that prove the advertised workflows.

This foundation benefits human developers even if they never use an AI agent. It improves CI/CD, platform engineering, disaster recovery, integrations, and reproducibility.

## The opportunity for Malaysian providers

Local cloud providers do not need to outbuild AWS service by service. They can compete on a different combination:

```text
Malaysian data residency and latency
    + transparent local economics
    + responsive human support
    + an open, programmable control plane
    + excellent agent and developer workflows
```

Human support can remain a differentiator. Its role should move upward—from performing routine control-plane changes to helping customers with architecture, migration, reliability, security, and exceptional situations.

The strategic risk is not merely that developers dislike an older console. Developers designing automated and agent-assisted workflows will tend to favour clouds that their tools can discover, operate, verify, and clean up without provider intervention. A provider that is invisible to those workflows may be excluded before price, sovereignty, or service quality is ever considered.

The next-generation cloud will not be the one with the most impressive chatbot. It will be the one whose entire platform can be safely operated as software.

---

*Methodology note: this article assesses customer-facing capabilities documented publicly as of 15 July 2026. “Not found in public materials” should not be read as proof that a provider lacks private or internal interfaces.*
