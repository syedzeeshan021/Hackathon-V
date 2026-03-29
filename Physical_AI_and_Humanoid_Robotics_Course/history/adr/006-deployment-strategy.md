# ADR-006: Deployment Strategy: Docusaurus (Static) & FastAPI (Containerized)

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2025-12-07
- **Feature:** 001-robotics-textbook-platform
- **Context:** Need a cost-effective and scalable deployment solution for a statically generated Docusaurus frontend and a FastAPI backend, leveraging free-tier options for the hackathon.

## Decision

Deploy the Docusaurus frontend as a static site to platforms like Vercel or GitHub Pages, and the FastAPI backend as a containerized application (e.g., to a serverless container platform).

## Consequences

### Positive

Cost-effective (free-tier options available), highly scalable for static content, clear separation of frontend/backend deployment concerns, leverages modern cloud practices.

### Negative

Increased complexity of managing two separate deployments, potential for CORS issues between frontend and backend if not configured correctly.

## Alternatives Considered

Full-stack framework deployment (e.g., Next.js on Vercel for both frontend and API routes): Rejected because Docusaurus is a documentation-specific static site generator, and the backend requires a Python environment. Monolithic deployment (e.g., a single server hosting both frontend and backend): Rejected due to less scalability for static assets and less clear separation of concerns.

## References

- Feature Spec: [spec.md](../../specs/001-robotics-textbook-platform/spec.md)
- Implementation Plan: [plan.md](../../specs/001-robotics-textbook-platform/plan.md)
- Related ADRs: N/A
- Evaluator Evidence: N/A
