---
# The client or product this engagement tests.
client: Acme Analytics
# Must equal the folder name under .projects/testing/.
engagement: acme-checkout
# One or both of api, ui.
surfaces: [api, ui]
# Required when ui is in surfaces.
ui_base_url: https://app.acme.test
# Required when api is in surfaces.
api_base_url: https://api.acme.test
# Optional: a path inside this engagement folder, commented out until the file exists.
# api_spec: specs/openapi.yaml
# Where the tests run, such as staging or a client test tenant.
environment: staging
# Optional: variable names only; their values live in this folder's .env.
credentials_env: [ACME_API_TOKEN]
---

## Background

Why the client engaged us and what the product does. Example: Acme sells subscriptions and wants its checkout tested before a pricing change.

## Scope

What this engagement tests, such as the checkout API and the payment page. Name the endpoints, pages, and flows in scope.

## Out of scope

What is explicitly not tested. Example: the admin console and third-party payment provider internals.

## Known risks

What could go wrong, in the client's words. Example: a pricing change may break cart totals for annual plans.

## Acceptance criteria

What a successful engagement looks like. Example: every checkout path has a passing API and UI test, and no open defect is above medium severity.

## Notes

- Replace every example with the engagement's facts; `engagement` must equal this file's folder name.
- `credentials_env` lists variable names only. Their values live in this engagement's `.env`, never in this brief, a document, a test, or a commit.
