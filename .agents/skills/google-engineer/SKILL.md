---
name: google-engineer
description: Embody Google-grade software engineering standards. Use this skill when designing, implementing, testing, refactoring, or reviewing production software to ensure clarity, simplicity, robust testing, maintainability, and clean architecture without over-engineering.
---

# Google Engineer Skill

A practical guide for applying Google-grade Software Engineering (SWE) principles to software development workflows.

> "Simplicity is prerequisite for reliability." — Edsger W. Dijkstra

## Core Tenets

1. **Do Not Overcomplicate Things**:
   - Prefer simple, readable, and direct solutions over clever abstractions.
   - Avoid premature optimization and unnecessary layers of indirection.
   - Do not build for hypothetical futures; build cleanly for today's requirements while leaving room for extension.

2. **Don't Reinvent the Wheel Without Good Reason**:
   - Leverage well-maintained standard libraries and battle-tested industry standard packages (e.g., SQLAlchemy, python-telegram-bot, pytest).
   - Only write custom primitives when third-party solutions are inadequate, insecure, or excessively bloated.

3. **Code as a Liability**:
   - Every line of code written is code that must be read, debugged, and maintained.
   - Strive to minimize boilerplate and unnecessary code.

4. **Hermetic & Comprehensive Testing**:
   - Write automated unit tests for business logic, edge cases, and failure modes.
   - Tests must be hermetic: reproducible, isolated, independent of external network or mutable shared state.

5. **Defensive Programming & Observability**:
   - Validate inputs at boundaries.
   - Use structured logging with appropriate log levels (DEBUG, INFO, WARNING, ERROR).
   - Ensure graceful degradation with informative user-facing error messages.

---

## Engineering Workflow

### Phase 1: Requirements & Problem Definition
- Read all existing documentation, requirements, and constraints.
- Identify the core data entities, API boundaries, and user interactions.
- Clarify assumptions and edge cases before writing code.

### Phase 2: Architecture & Data Modeling
- Decouple layers cleanly:
  - **Data Access Layer**: Database models, migrations, and session lifecycle.
  - **Domain / Service Layer**: Pure business logic (e.g., parsing, metrics calculation, leaderboard ranking).
  - **Interface / Presentation Layer**: Transport handlers (e.g., Telegram command handlers, REST endpoints, CLI).
- Enforce strict typing with type annotations across all function signatures.

### Phase 3: Implementation
- Write idiomatic code adhering to PEP 8 / Google Python Style Guide.
- Ensure database connections and sessions are safely managed with context managers.
- Keep functions small and focused on a single responsibility.

### Phase 4: Automated Testing
- Use `pytest` for all unit and integration tests.
- Mock network calls and external services.
- Test both the "happy path" and adverse scenarios (e.g., unregistered users, malformed inputs, boundary dates).

### Phase 5: Documentation & CI/CD
- Write clear, concise documentation (README, Wiki, inline docstrings).
- Include setup guides, configuration examples, and architecture overviews.
- Configure continuous integration (GitHub Actions) to automate linting and test execution.

---

## Pre-Commit / Pre-Delivery Checklist

Before considering any task complete:
- [ ] Code is formatted and lint-free.
- [ ] Type hints are consistent and clear.
- [ ] All unit and integration tests pass cleanly.
- [ ] No hardcoded secrets or credentials exist in the codebase.
- [ ] Error messages are actionable and graceful.
- [ ] Documentation and user guides reflect current functionality.
