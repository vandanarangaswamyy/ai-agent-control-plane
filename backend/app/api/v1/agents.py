from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_agent_registry_service
from app.schemas.agents import (
    AgentCreate,
    AgentRead,
    AgentVersionCreate,
    AgentVersionRead,
    AgentVersionUpdate,
)
from app.services.agent_registry import AgentRegistryService

router = APIRouter(prefix="/agents", tags=["agents"])

LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
AgentRegistryDependency = Annotated[AgentRegistryService, Depends(get_agent_registry_service)]


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentCreate,
    service: AgentRegistryDependency,
) -> AgentRead:
    agent = service.create_agent(
        name=payload.name,
        description=payload.description,
        owner=payload.owner,
    )
    return AgentRead.model_validate(agent)


@router.get("", response_model=list[AgentRead])
def list_agents(
    service: AgentRegistryDependency,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[AgentRead]:
    agents = service.list_agents(limit=limit, offset=offset)
    return [AgentRead.model_validate(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(
    agent_id: uuid.UUID,
    service: AgentRegistryDependency,
) -> AgentRead:
    agent = service.get_agent(agent_id)
    return AgentRead.model_validate(agent)


@router.post(
    "/{agent_id}/versions",
    response_model=AgentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_version(
    agent_id: uuid.UUID,
    payload: AgentVersionCreate,
    service: AgentRegistryDependency,
) -> AgentVersionRead:
    agent_version = service.create_version(
        agent_id=agent_id,
        name=payload.name,
        prompt=payload.prompt,
        model=payload.model,
        tool_config=payload.tool_config,
        runtime_config=payload.runtime_config,
    )
    return AgentVersionRead.model_validate(agent_version)


@router.get("/{agent_id}/versions", response_model=list[AgentVersionRead])
def list_agent_versions(
    agent_id: uuid.UUID,
    service: AgentRegistryDependency,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[AgentVersionRead]:
    versions = service.list_versions(agent_id=agent_id, limit=limit, offset=offset)
    return [AgentVersionRead.model_validate(version) for version in versions]


@router.patch("/{agent_id}/versions/{version_id}", response_model=AgentVersionRead)
def update_agent_version(
    agent_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: AgentVersionUpdate,
    service: AgentRegistryDependency,
) -> AgentVersionRead:
    agent_version = service.update_draft_version(
        agent_id=agent_id,
        version_id=version_id,
        update_fields=payload.model_dump(exclude_unset=True),
    )
    return AgentVersionRead.model_validate(agent_version)


@router.post("/{agent_id}/versions/{version_id}/deprecate", response_model=AgentVersionRead)
def deprecate_agent_version(
    agent_id: uuid.UUID,
    version_id: uuid.UUID,
    service: AgentRegistryDependency,
) -> AgentVersionRead:
    agent_version = service.deprecate_version(agent_id=agent_id, version_id=version_id)
    return AgentVersionRead.model_validate(agent_version)
