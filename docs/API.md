# API reference

Interactive OpenAPI documentation is served at `/docs`; the raw schema is
available at `/openapi.json`.

## `POST /api/ask`

Submit one policy question.

```bash
curl --fail-with-body http://127.0.0.1:8000/api/ask \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  --data '{"question":"How long does a card refund take?"}'
```

Example response:

```json
{
  "request_id": "0ed7e07dc95b4980982911161d3d952d",
  "latency_ms": 1.24,
  "answer": "Card refunds are issued within 5 to 10 business days. [REF-001]",
  "citations": [
    {
      "document_id": "REF-001",
      "title": "Refund processing times",
      "source": "/policies/REF-001",
      "score": 0.4821
    }
  ],
  "refused": false,
  "backend": "extractive",
  "model": null,
  "finish_reason": null,
  "prompt_tokens": null,
  "completion_tokens": null
}
```

Questions are trimmed, must contain a letter or number, and must be between 3
and 2,000 characters. Validation errors use FastAPI's standard HTTP 422 shape.
A refusal is a successful HTTP 200 response with `refused: true`, a stable
refusal message, and an empty citation list.

## Discovery

### `GET /api/meta`

Returns the running version, backend, policy count, capabilities, and links.
The browser uses this endpoint for its live runtime indicator.

### `GET /api/policies`

Returns policy IDs, titles, and source paths without duplicating full policy
text. Human-readable policy pages are available at `/policies` and
`/policies/{document_id}`.

## Operations

### `GET /health`

Returns status, application version, loaded-document count, and backend. It is
appropriate for container health and basic readiness checks. It does not test
an optional external inference provider on every request.

## Headers and caching

All routes receive defensive content-type, framing, referrer, permissions, and
Content Security Policy headers. `/api/*` responses use `Cache-Control:
no-store`. VSA does not enable cross-origin requests by default; clients should
use the same origin or add a narrowly reviewed CORS policy at deployment time.

## Authentication and rate limits

This synthetic local demo has no user authentication or application-level rate
limiter. Do not expose it as a real customer service without adding an identity
boundary, authorization, reverse-proxy limits, abuse monitoring, and an
approved data-retention policy.