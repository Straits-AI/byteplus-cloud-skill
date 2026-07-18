# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/) for its public-preview releases.

## [Unreleased]

### Added

- Managed-service readiness guidance for activation gates, service-linked roles,
  enum/AZ/spec discovery, and opaque first-create failures.
- A concrete Kafka/KMS preflight and dependency-aware Kafka cleanup runbook based
  on current official documentation and live `bp` 1.0.17 help.

### Changed

- Require JSON `--body` for nested object/array CLI input and a protected SDK path
  when the request contains secrets.
- Treat pagination, value formats, and JavaScript-rendered documentation as
  explicit retrieval checks instead of retry-time discoveries.

## [0.1.0] - 2026-07-14

### Added

- Initial `byteplus-cloud` Agent Skill with progressive product references.
- Safe official `bp` CLI discovery and checksum-verified installation helpers.
- BytePlus doctor and action-catalog helpers.
- Bounded Seed Speech TTS smoke helper with secret-safe parsing.
- ECS/VPC, veFaaS, Cloud Sandbox, ModelArk, AgentKit, Edge Functions, TOS, VKE,
  database, IaC, observability, security, and operations guidance.
- Offline unit, secret-safety, structure, and evaluation-contract tests.
- Sanitized public validation matrix and open-source contribution policies.

[Unreleased]: https://github.com/Straits-AI/byteplus-cloud-skill/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Straits-AI/byteplus-cloud-skill/releases/tag/v0.1.0
