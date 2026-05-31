# Architectural Decisions

## ADR-001
Business logic lives in services

Reason:
Prevent API routes from becoming fat controllers.

Status:
Accepted

---

## ADR-002
Runtime uses SafetyGateway for all tool execution

Reason:
Tool execution must be policy-gated and auditable.

Status:
Accepted

---

## ADR-003
Tools are mocks during MVP

Reason:
Infrastructure is more important than provider integrations.

Status:
Accepted

---

## ADR-004
Observability implemented before Evaluation Harness

Reason:
Evaluations depend on execution visibility.

Status:
Accepted

---

## ADR-005
Observability uses local in-memory export with Prometheus exposition for MVP

Reason:
The milestone needed actionable visibility without introducing external collector or metrics infrastructure complexity.

Status:
Accepted

Status:
Accepted
