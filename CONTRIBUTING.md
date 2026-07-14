# Contributing

Thank you for helping make BytePlus automation safer and more reproducible for
coding agents.

## Before starting

- Search existing issues and pull requests.
- Open a capability-gap or feature issue before a large new product workflow.
- Never use a production account for project validation.
- Never paste credentials, profile files, signed URLs, private prompts, generated
  content, account IDs, exact live resource IDs, or raw provider responses into a
  public issue or pull request.

## Development setup

The repository uses Python standard-library helpers and `unittest`. Python 3.10+
is required.

```bash
git clone https://github.com/Straits-AI/byteplus-cloud-skill.git
cd byteplus-cloud-skill
python3 -m unittest discover -s tests -v
python3 -m compileall -q skills/byteplus-cloud/scripts
python3 scripts/check_public_tree.py
```

Optional linting uses the version pinned in CI:

```bash
python3 -m pip install ruff==0.15.2
ruff check skills tests scripts
```

## Skill design rules

- Keep `SKILL.md` concise and route detailed product procedures through direct
  references.
- Retrieve volatile API names, flags, models, prices, limits, and regions from
  current official sources; do not freeze them into prose or scripts.
- Prefer official CLI, provider, SDK, API, or product MCP interfaces.
- Preserve effect-based approval gates, credential isolation, read-before-write,
  deterministic ownership, three-layer verification, and exact cleanup.
- Do not claim public HTTP, successful deployment, or `CLEAN` without the matching
  proof.
- Keep UI steps limited to documented owner-controlled prerequisites for which no
  current programmatic surface exists.

The skill frontmatter intentionally contains only `name` and `description` for
portable Agent Skills compatibility.

## Tests and evaluations

Every behavior change should include the smallest useful offline regression.
Tests must not contact BytePlus, depend on a local credential profile, or mutate
cloud state.

For a new live-validated capability, maintainers should privately retain:

- the exact profile class and region, with account identity redacted;
- starting inventory and ownership boundary;
- current source/schema retrieval;
- create and invocation evidence;
- control-plane, data-plane, and operations verification; and
- dependency-ordered deletion plus fresh absence checks.

Publish only a sanitized capability result in
[`docs/validation-matrix.md`](docs/validation-matrix.md).

## Pull requests

Pull requests should explain:

- the problem and user impact;
- the official sources or schemas used;
- safety and compatibility effects;
- tests performed; and
- whether the capability is guidance, live partial, or live E2E.

Keep pull requests focused. By contributing, you agree that your contribution is
licensed under the Apache License 2.0.
