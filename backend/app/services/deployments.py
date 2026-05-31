from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.telemetry import get_tracer
from app.db.models.agent import AgentVersion
from app.db.models.deployment import DeploymentEvent
from app.domain.enums import (
    AgentVersionLifecycle,
    DeploymentEventType,
    EvaluationStatus,
    TraceEventType,
)
from app.domain.errors import BusinessRuleViolationError, NotFoundError
from app.repositories.agents import AgentRepository
from app.repositories.deployments import DeploymentRepository
from app.repositories.evaluations import EvaluationRepository
from app.repositories.runtime import RuntimeRepository
from app.schemas.deployments import (
    DeploymentPromotionRead,
    DeploymentRollbackRead,
)


class DeploymentService:
    """Business workflows for deployment promotion, rollback, and history."""

    def __init__(
        self,
        *,
        session: Session,
        agent_repository: AgentRepository,
        evaluation_repository: EvaluationRepository,
        deployment_repository: DeploymentRepository,
        runtime_repository: RuntimeRepository,
        minimum_success_rate: Decimal,
    ) -> None:
        self._session = session
        self._agent_repository = agent_repository
        self._evaluation_repository = evaluation_repository
        self._deployment_repository = deployment_repository
        self._runtime_repository = runtime_repository
        self._minimum_success_rate = minimum_success_rate

    def promote_version(
        self,
        *,
        agent_id: uuid.UUID,
        agent_version_id: uuid.UUID,
        reason: str | None,
    ) -> DeploymentPromotionRead:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("deployment.promote") as span:
            try:
                span.set_attribute("agent_id", str(agent_id))
                span.set_attribute("agent_version_id", str(agent_version_id))
                agent = self._agent_repository.get_agent_for_update(agent_id)
                if agent is None:
                    raise NotFoundError("agent not found")

                target_version = self._agent_repository.get_version_for_agent(
                    agent_id=agent_id,
                    version_id=agent_version_id,
                )
                if target_version is None:
                    raise NotFoundError("agent version not found")
                if target_version.lifecycle == AgentVersionLifecycle.DEPRECATED:
                    raise BusinessRuleViolationError("deprecated versions cannot be promoted")

                evaluation = (
                    self._evaluation_repository.get_latest_completed_evaluation_for_version(
                        agent_version_id
                    )
                )
                if evaluation is None:
                    raise BusinessRuleViolationError(
                        "latest evaluation is required before promotion"
                    )
                if evaluation.status != EvaluationStatus.PASSED:
                    raise BusinessRuleViolationError("latest evaluation must pass before promotion")
                if (
                    evaluation.success_rate is None
                    or evaluation.success_rate <= self._minimum_success_rate
                ):
                    raise BusinessRuleViolationError(
                        "evaluation success rate must exceed threshold"
                    )

                current_production = self._deployment_repository.get_current_production_version(
                    agent_id
                )
                if current_production is not None and current_production.id == target_version.id:
                    raise BusinessRuleViolationError("version is already production")

                if current_production is not None:
                    current_production.lifecycle = AgentVersionLifecycle.APPROVED
                    self._session.flush()

                target_version.lifecycle = AgentVersionLifecycle.PRODUCTION
                self._session.flush()

                deployment_event = self._deployment_repository.create_event(
                    agent_id=agent_id,
                    event_type=DeploymentEventType.PROMOTE,
                    source_version_id=(
                        current_production.id if current_production is not None else None
                    ),
                    target_version_id=target_version.id,
                    reason=reason or "promotion criteria satisfied",
                    trace_id=uuid.uuid4().hex,
                )
                self._trace_deployment(
                    event=deployment_event,
                    name="DeploymentPromoted",
                    attributes={
                        "agent_id": str(agent_id),
                        "source_version_id": (
                            str(current_production.id) if current_production is not None else None
                        ),
                        "target_version_id": str(target_version.id),
                        "reason": deployment_event.reason,
                    },
                )
                self._session.commit()
                self._session.refresh(deployment_event)
                span.set_attribute("deployment.event_id", str(deployment_event.id))
                return DeploymentPromotionRead(
                    agent_id=agent_id,
                    version_promoted=target_version.id,
                    previous_production_version=(
                        current_production.id if current_production is not None else None
                    ),
                    deployment_timestamp=deployment_event.created_at,
                )
            except Exception as exc:
                self._session.rollback()
                span.record_exception(exc)
                raise

    def rollback(
        self,
        *,
        agent_id: uuid.UUID,
        reason: str | None,
    ) -> DeploymentRollbackRead:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("deployment.rollback") as span:
            try:
                span.set_attribute("agent_id", str(agent_id))
                agent = self._agent_repository.get_agent_for_update(agent_id)
                if agent is None:
                    raise NotFoundError("agent not found")

                current_production = self._deployment_repository.get_current_production_version(
                    agent_id
                )
                if current_production is None:
                    raise BusinessRuleViolationError("no production version is available")

                restored_version = self._select_previous_version_for_rollback(
                    agent_id=agent_id,
                    current_version_id=current_production.id,
                )
                if restored_version is None:
                    raise BusinessRuleViolationError(
                        "no previous production-capable version is available for rollback"
                    )

                current_production.lifecycle = AgentVersionLifecycle.APPROVED
                self._session.flush()
                restored_version.lifecycle = AgentVersionLifecycle.PRODUCTION
                self._session.flush()

                deployment_event = self._deployment_repository.create_event(
                    agent_id=agent_id,
                    event_type=DeploymentEventType.ROLLBACK,
                    source_version_id=current_production.id,
                    target_version_id=restored_version.id,
                    reason=reason or "rollback to previous production-capable version",
                    trace_id=uuid.uuid4().hex,
                )
                self._trace_deployment(
                    event=deployment_event,
                    name="DeploymentRolledBack",
                    attributes={
                        "agent_id": str(agent_id),
                        "source_version_id": str(current_production.id),
                        "target_version_id": str(restored_version.id),
                        "reason": deployment_event.reason,
                    },
                )
                self._session.commit()
                self._session.refresh(deployment_event)
                span.set_attribute("deployment.event_id", str(deployment_event.id))
                return DeploymentRollbackRead(
                    agent_id=agent_id,
                    version_restored=restored_version.id,
                    rollback_timestamp=deployment_event.created_at,
                )
            except Exception as exc:
                self._session.rollback()
                span.record_exception(exc)
                raise

    def list_deployment_events(self, *, agent_id: uuid.UUID) -> list[DeploymentEvent]:
        agent = self._agent_repository.get_agent(agent_id)
        if agent is None:
            raise NotFoundError("agent not found")
        return self._deployment_repository.list_events_for_agent(agent_id)

    def _select_previous_version_for_rollback(
        self,
        *,
        agent_id: uuid.UUID,
        current_version_id: uuid.UUID,
    ) -> AgentVersion | None:
        for event in self._deployment_repository.list_promote_events_for_agent(agent_id):
            if event.target_version_id is None or event.target_version_id == current_version_id:
                continue
            candidate = self._agent_repository.get_version_for_agent(
                agent_id=agent_id,
                version_id=event.target_version_id,
            )
            if candidate is None or candidate.lifecycle == AgentVersionLifecycle.DEPRECATED:
                continue
            return candidate
        return None

    def _trace_deployment(
        self,
        *,
        event: DeploymentEvent,
        name: str,
        attributes: dict[str, object],
    ) -> None:
        self._runtime_repository.create_trace(
            trace_id=event.trace_id or uuid.uuid4().hex,
            event_type=TraceEventType.DEPLOYMENT,
            entity_type="deployment",
            entity_id=event.id,
            name=name,
            attributes=attributes,
        )
