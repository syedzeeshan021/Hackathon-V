# ADR-007: Testing Frameworks: Jest/RTL & Pytest

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2025-12-07
- **Feature:** 001-robotics-textbook-platform
- **Context:** Need robust testing frameworks for both frontend (React/Docusaurus) and backend (FastAPI/Python) to ensure code quality, functionality, and maintainability.

## Decision

Use Jest and React Testing Library (RTL) for frontend testing, and Pytest for backend testing.

## Consequences

### Positive

Leverages well-established and widely-adopted testing tools for each ecosystem, provides comprehensive testing capabilities (unit, integration, component), good community support and documentation.

### Negative

Requires developers to be familiar with two distinct testing frameworks, potential for inconsistencies in testing methodologies if not standardized.

## Alternatives Considered

Cypress/Playwright (End-to-End testing for frontend): While valuable, these were not chosen as primary frameworks to simplify the initial testing setup and focus on unit/integration testing within the hackathon scope. Other Python testing frameworks (e.g., unittest): Rejected due to Pytest's more flexible and readable syntax, and extensive plugin ecosystem.

## References

- Feature Spec: [spec.md](../../specs/001-robotics-textbook-platform/spec.md)
- Implementation Plan: [plan.md](../../specs/001-robotics-textbook-platform/plan.md)
- Related ADRs: N/A
- Evaluator Evidence: N/A
