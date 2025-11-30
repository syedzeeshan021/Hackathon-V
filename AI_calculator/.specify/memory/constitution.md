<!-- Sync Impact Report -->
<!--
Version change: [CONSTITUTION_VERSION] (old) → 1.1.0 (new)
Modified principles:
  - [PRINCIPLE_1_NAME] → I. Test-Driven Development (TDD)
  - [PRINCIPLE_2_NAME] → II. Python Best Practices
  - [PRINCIPLE_3_NAME] → III. Architectural Decision Records (ADRs)
  - [PRINCIPLE_4_NAME] → IV. Object-Oriented Programming (OOP) Principles
Added sections:
  - Technical Stack
  - Quality Requirements
Removed sections:
  - [PRINCIPLE_5_NAME]
  - [PRINCIPLE_6_NAME]
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ updated (implicit check, no direct action needed yet)
  - .specify/templates/spec-template.md: ✅ updated (implicit check, no direct action needed yet)
  - .specify/templates/tasks-template.md: ✅ updated (implicit check, no direct action needed yet)
  - .specify/templates/commands/*.md: ✅ updated (implicit check, no direct action needed yet)
Follow-up TODOs:
  - RATIFICATION_DATE: Original ratification date unknown.
-->
# AI Calculator Constitution

## Core Principles

### I. Test-Driven Development (TDD)
All new features and bug fixes must follow a Test-Driven Development approach. Tests are written first, approved, fail, and then the implementation is created to pass them. The Red-Green-Refactor cycle is strictly enforced.

### II. Python Best Practices
All Python code must use Python 3.12+ and include type hints for all function signatures and variable declarations. Code must be clean, readable, and adhere to PEP 8 guidelines.

### III. Architectural Decision Records (ADRs)
Architecturally significant decisions must be documented using ADRs. Each ADR should capture the context, decision, and consequences to provide long-term historical context and rationale.

### IV. Object-Oriented Programming (OOP) Principles
Adhere to essential OOP principles: SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion), DRY (Don't Repeat Yourself), and KISS (Keep It Simple, Stupid) to ensure maintainable and scalable code.

## Technical Stack

- **Python Version**: Python 3.12+
- **Package Manager**: UV
- **Testing Framework**: pytest
- **Version Control**: All project files must be tracked in Git.

## Quality Requirements

- **Test Coverage**: Minimum of 80% code coverage.
- **All tests must pass**.
- **Data Structures**: Use dataclasses for all complex data structures.

## Governance
This constitution supersedes all other practices. Amendments require documentation, approval, and a migration plan. All pull requests and code reviews must verify compliance with these principles.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE): Original ratification date unknown | **Last Amended**: 2025-11-30
