# Security policy

## Supported version

The project is in public preview. Security fixes are applied to the latest commit
on `main` and the latest tagged preview release.

## Report a vulnerability privately

Use GitHub's **Report a vulnerability** action in this repository's Security tab.
Do not open a public issue for a suspected credential leak, instruction-injection
path, command-injection issue, unsafe cloud mutation, or dependency compromise.

Include:

- the affected file and revision;
- a minimal reproduction using fake credentials and disposable fixtures;
- the impact and expected safe behavior; and
- any suggested remediation.

Do not include real BytePlus credentials, profile files, session tokens, API keys,
signed URLs, customer data, or account/resource identifiers. Maintainers will
acknowledge the report, investigate, and coordinate disclosure through the private
advisory.

Vulnerabilities in BytePlus products or APIs should be reported through
BytePlus's official security process. This repository can address only its own
instructions, scripts, packaging, and project infrastructure.
