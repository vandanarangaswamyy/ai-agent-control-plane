from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models.approval import ApprovalRequest
from app.domain.enums import ApprovalStatus, PolicyDecision


class ApprovalRepository:
    """Persistence operations for approval requests."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_approval_request(
        self,
        *,
        agent_run_id: uuid.UUID,
        tool_call_id: uuid.UUID,
        reason: str,
        requested_action: dict[str, object],
        requested_by: str | None = None,
    ) -> ApprovalRequest:
        approval = ApprovalRequest(
            agent_run_id=agent_run_id,
            tool_call_id=tool_call_id,
            policy_decision=PolicyDecision.REQUIRE_APPROVAL,
            reason=reason,
            requested_action=requested_action,
            requested_by=requested_by,
        )
        self._session.add(approval)
        self._session.flush()
        return approval

    def list_approval_requests(self, *, limit: int, offset: int) -> list[ApprovalRequest]:
        statement: Select[tuple[ApprovalRequest]] = (
            select(ApprovalRequest)
            .order_by(ApprovalRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def get_approval_request(self, approval_id: uuid.UUID) -> ApprovalRequest | None:
        return self._session.get(ApprovalRequest, approval_id)

    def get_approval_request_for_update(
        self,
        approval_id: uuid.UUID,
    ) -> ApprovalRequest | None:
        statement = (
            select(ApprovalRequest).where(ApprovalRequest.id == approval_id).with_for_update()
        )
        return self._session.scalars(statement).one_or_none()

    def list_approval_requests_for_run(
        self,
        run_id: uuid.UUID,
        *,
        status: ApprovalStatus | None = None,
    ) -> list[ApprovalRequest]:
        statement = select(ApprovalRequest).where(ApprovalRequest.agent_run_id == run_id)
        if status is not None:
            statement = statement.where(ApprovalRequest.status == status)
        statement = statement.order_by(ApprovalRequest.created_at.asc(), ApprovalRequest.id.asc())
        return list(self._session.scalars(statement).all())

    def flush(self) -> None:
        self._session.flush()
