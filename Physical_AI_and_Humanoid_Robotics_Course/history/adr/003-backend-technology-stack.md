# ADR-003: Backend Technology Stack: FastAPI, Python 3.11

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2025-12-07
- **Feature:** 001-robotics-textbook-platform
- **Context:** Need a high-performance and easy-to-develop backend for the API, capable of handling various services like chat, personalization, and translation.

## Decision

Use FastAPI for the web framework and Python 3.11 as the language.

## Consequences

### Positive

High performance (async support), excellent developer experience (Pydantic, OpenAPI auto-docs), large ecosystem.

### Negative

Can be memory-intensive for certain workloads compared to lower-level languages.

## Alternatives Considered

Django (Python web framework): Rejected due to its larger footprint and opinionated structure, which is overkill for API-only backend. Node.js/Express.js (JavaScript/TypeScript): Rejected due to preference for Python ecosystem for AI/ML related tasks (RAG chatbot).

## References

- Feature Spec: [spec.md](../../specs/001-robotics-textbook-platform/spec.md)
- Implementation Plan: [plan.md](../../specs/001-robotics-textbook-platform/plan.md)
- Related ADRs: N/A
- Evaluator Evidence: N/A
