# ADR-004: Database & Vector Store: Neon Postgres & Qdrant Cloud

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2025-12-07
- **Feature:** 001-robotics-textbook-platform
- **Context:** Requires a relational database for user data and personalization settings, and a vector store optimized for similarity search for the RAG chatbot. Both need to be cost-effective (free-tier capable).

## Decision

Use Neon Serverless Postgres for user data and personalization settings, and Qdrant Cloud (Free Tier) for vector embeddings for the RAG chatbot.

## Consequences

### Positive

Cost-effective due to free-tier availability, specialized tools for specific data types (relational vs. vector), scalable serverless architecture for Postgres.

### Negative

Increased complexity due to managing two distinct data stores, potential for vendor lock-in with specific cloud providers.

## Alternatives Considered

Single database solution (e.g., Postgres with pgvector extension): Rejected because Qdrant offers more advanced vector search capabilities and better performance for vector-specific workloads. Other cloud-managed databases (e.g., AWS RDS, Azure SQL): Rejected due to higher costs for the free tier and less specialized vector search features.

## References

- Feature Spec: [spec.md](../../specs/001-robotics-textbook-platform/spec.md)
- Implementation Plan: [plan.md](../../specs/001-robotics-textbook-platform/plan.md)
- Related ADRs: N/A
- Evaluator Evidence: N/A
