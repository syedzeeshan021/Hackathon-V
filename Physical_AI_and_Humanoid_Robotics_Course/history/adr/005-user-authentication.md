# ADR-005: User Authentication: Better-Auth.com

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2025-12-07
- **Feature:** 001-robotics-textbook-platform
- **Context:** Need a secure and easy-to-implement user authentication system, with support for signup, signin, and password reset functionality, preferably leveraging an external service to reduce development overhead.

## Decision

Integrate Better-Auth.com as the external authentication service.

## Consequences

### Positive

Reduced development time and effort for authentication features, offloads security concerns to a specialized provider, provides robust features like password reset out-of-the-box.

### Negative

Vendor lock-in with Better-Auth.com, potential costs associated with usage tiers, reliance on an external service for core functionality.

## Alternatives Considered

Self-hosted authentication (e.g., using JWTs and custom database storage): Rejected due to increased security risks, development complexity, and maintenance overhead. Other OAuth/OpenID Connect providers (e.g., Auth0, Firebase Authentication): Rejected due to Better-Auth.com being identified as a suitable free-tier option for hackathon purposes.

## References

- Feature Spec: [spec.md](../../specs/001-robotics-textbook-platform/spec.md)
- Implementation Plan: [plan.md](../../specs/001-robotics-textbook-platform/plan.md)
- Related ADRs: N/A
- Evaluator Evidence: N/A
