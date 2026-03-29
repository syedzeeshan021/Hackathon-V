# ADR-001: Overall Architecture: Monorepo Structure

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2025-12-07
- **Feature:** 001-robotics-textbook-platform
- **Context:** Project requires clear separation of frontend and backend while maintaining ease of development and shared configuration.

## Decision

Monorepo with `frontend` directory for Docusaurus/React application and `backend` directory for FastAPI application.

## Consequences

### Positive

Simplified shared configuration, easier cross-service communication, single repository for version control, unified CI/CD.

### Negative

Can become complex with many services, potential for tight coupling if not managed well.

## Alternatives Considered

Separate repositories for frontend and backend: More clear separation of concerns, independent deployment. Rejected due to increased overhead for shared configuration and local development.

## References

- Feature Spec: [spec.md](../../specs/001-robotics-textbook-platform/spec.md)
- Implementation Plan: [plan.md](../../specs/001-robotics-textbook-platform/plan.md)
- Related ADRs: N/A
- Evaluator Evidence: N/A
