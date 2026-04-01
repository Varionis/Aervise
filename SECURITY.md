# Security Policy

## Scope

This repository is public. Treat all code, docs, issue comments, pull requests, and examples as publicly visible.

Do not commit:

- API keys
- access tokens
- `.env` files with real values
- production URLs with embedded credentials
- user PII
- raw request logs or traces that contain identifiable user data

## Supported Hygiene

Current repo expectations:

- secrets stay server-side only
- `.env.example` may document variable names, but must never contain real values
- `logs/` and `traces/` are local runtime artifacts and must not be committed
- fallback snapshots used for local debugging must stay out of version control unless fully sanitized

## Reporting a Vulnerability

If you find a security issue, do not open a public issue with exploit details.

Report it privately to the project maintainer first. Include:

- affected file or area
- impact
- reproduction steps
- suggested mitigation if known

Until a dedicated security contact is added, use a private direct channel with the maintainer instead of public disclosure.

## Public Repo Notes

Because this repo documents architecture and system behavior, be careful with:

- debug endpoints
- rate-limit assumptions
- provider usage patterns
- observability payloads

Architecture visibility is acceptable. Secret leakage is not.

## Operational Guidance

Before pushing:

1. verify `.env` and similar files are ignored
2. verify logs and traces are not staged
3. verify no tokens or credentials appear in tests, docs, or scripts
4. run the configured secret scan if available

## Disclaimer

This project is an explainable environmental decision system, not a medical device or emergency service.
