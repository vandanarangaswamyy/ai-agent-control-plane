from __future__ import annotations

from fastapi.testclient import TestClient

from app.domain.enums import AgentVersionLifecycle


def create_agent(client: TestClient, *, name: str = "research-agent") -> dict[str, object]:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": name,
            "description": "Research workflow agent",
            "owner": "platform",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_version(
    client: TestClient,
    *,
    agent_id: str,
    name: str = "initial",
    prompt: str = "Summarize the input",
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/agents/{agent_id}/versions",
        json={
            "name": name,
            "prompt": prompt,
            "model": "claude-sonnet-4",
            "tool_config": {"file": {"enabled": True}},
            "runtime_config": {"temperature": 0},
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_list_and_get_agent(client: TestClient) -> None:
    agent = create_agent(client)

    list_response = client.get("/api/v1/agents")
    get_response = client.get(f"/api/v1/agents/{agent['id']}")

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [agent["id"]]
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "research-agent"


def test_agent_names_must_be_unique(client: TestClient) -> None:
    create_agent(client)

    response = client.post(
        "/api/v1/agents",
        json={
            "name": "research-agent",
            "description": "Duplicate",
            "owner": "platform",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["type"] == "ConflictError"


def test_agent_names_are_unique_case_insensitively(client: TestClient) -> None:
    create_agent(client, name="Research-Agent")

    response = client.post(
        "/api/v1/agents",
        json={
            "name": "research-agent",
            "description": "Duplicate with different case",
            "owner": "platform",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["type"] == "ConflictError"


def test_agent_name_is_trimmed_and_cannot_be_blank(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "  trimmed-agent  ",
            "description": "Whitespace should be trimmed",
            "owner": " platform ",
        },
    )
    blank_response = client.post(
        "/api/v1/agents",
        json={
            "name": "   ",
            "description": "Blank name",
            "owner": "platform",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "trimmed-agent"
    assert response.json()["owner"] == "platform"
    assert blank_response.status_code == 422


def test_create_versions_auto_increments_per_agent(client: TestClient) -> None:
    agent = create_agent(client)

    first_version = create_version(client, agent_id=str(agent["id"]), name="v1")
    second_version = create_version(client, agent_id=str(agent["id"]), name="v2")

    assert first_version["version"] == 1
    assert first_version["lifecycle"] == AgentVersionLifecycle.DRAFT
    assert second_version["version"] == 2


def test_list_versions_for_agent(client: TestClient) -> None:
    agent = create_agent(client)
    create_version(client, agent_id=str(agent["id"]), name="v1")
    create_version(client, agent_id=str(agent["id"]), name="v2")

    response = client.get(f"/api/v1/agents/{agent['id']}/versions")

    assert response.status_code == 200
    assert [item["version"] for item in response.json()] == [2, 1]


def test_update_draft_version_metadata(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_version(client, agent_id=str(agent["id"]))

    response = client.patch(
        f"/api/v1/agents/{agent['id']}/versions/{version['id']}",
        json={
            "name": "edited",
            "prompt": "Use the latest approved instructions",
            "runtime_config": {"temperature": 0.2},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "edited"
    assert body["prompt"] == "Use the latest approved instructions"
    assert body["runtime_config"] == {"temperature": 0.2}


def test_deprecated_versions_cannot_be_edited(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_version(client, agent_id=str(agent["id"]))

    deprecate_response = client.post(
        f"/api/v1/agents/{agent['id']}/versions/{version['id']}/deprecate"
    )
    update_response = client.patch(
        f"/api/v1/agents/{agent['id']}/versions/{version['id']}",
        json={"name": "should-fail"},
    )

    assert deprecate_response.status_code == 200
    assert deprecate_response.json()["lifecycle"] == AgentVersionLifecycle.DEPRECATED
    assert update_response.status_code == 422
    assert update_response.json()["error"]["message"] == "only DRAFT versions can be edited"


def test_invalid_deprecate_transition_is_rejected(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_version(client, agent_id=str(agent["id"]))

    first_response = client.post(
        f"/api/v1/agents/{agent['id']}/versions/{version['id']}/deprecate"
    )
    second_response = client.post(
        f"/api/v1/agents/{agent['id']}/versions/{version['id']}/deprecate"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["error"]["type"] == "InvalidStateTransitionError"


def test_missing_agent_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/agents/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "NotFoundError"
