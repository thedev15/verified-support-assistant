# Security policy

## Supported version

Security fixes are applied to the latest code on `main`. This repository is a
synthetic demonstration and is not a production customer-support service.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private
data, or active attack instructions. Use GitHub's private vulnerability
reporting for this repository when available, or contact the repository owner
privately through their GitHub profile. Include affected version, reproduction
steps, impact, and a minimal proof of concept.

## Scope and safe operation

- Never submit real customer, order, payment, authentication, or health data.
- Never commit W&B keys, GitHub tokens, `.env`, browser profiles, or service
  credentials.
- The local server binds to loopback by default; review authentication, TLS,
  proxy, CORS, and rate limits before network exposure.
- Optional Forge Inference and Weave tracing send question content to the
  configured project. Enable them only under an approved data policy.
- Policy guardrails and TF-IDF thresholds reduce unsupported answers but are
  not a security boundary against every adversarial input.

The application sets a same-origin Content Security Policy, blocks framing,
disables unnecessary browser capabilities, prevents API caching, validates
configuration on startup, and renders API data with text-only DOM operations.
A production deployment still requires authentication, authorization, abuse
controls, dependency monitoring, centralized secret management, audit logging,
privacy review, and incident response.