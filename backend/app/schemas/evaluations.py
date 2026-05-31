from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain.enums import EvaluationResultStatus, EvaluationStatus

SuiteName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
CaseName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
TaskText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ToolName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class EvaluationSuiteCase(BaseModel):
    """One executable case within a suite definition."""

    model_config = ConfigDict(extra="forbid")

    name: CaseName
    task: TaskText
    tool_name: ToolName | None = None
    expected_tool_name: ToolName | None = None


class EvaluationSuiteDefinition(BaseModel):
    """JSON-based suite format stored under evals/suites."""

    model_config = ConfigDict(extra="forbid")

    name: SuiteName
    cases: list[EvaluationSuiteCase]

    @model_validator(mode="after")
    def validate_cases(self) -> EvaluationSuiteDefinition:
        if not self.cases:
            raise ValueError("suite must contain at least one case")
        case_names = [case.name for case in self.cases]
        if len(case_names) != len(set(case_names)):
            raise ValueError("suite case names must be unique")
        return self


class EvaluationCreateRequest(BaseModel):
    """Request body for running an evaluation."""

    model_config = ConfigDict(extra="forbid")

    agent_version_id: uuid.UUID
    suite_name: SuiteName


class EvaluationCompareRequest(BaseModel):
    """Request body for comparing two agent versions."""

    model_config = ConfigDict(extra="forbid")

    base_agent_version_id: uuid.UUID
    candidate_agent_version_id: uuid.UUID
    suite_name: SuiteName


class EvaluationResultRead(BaseModel):
    """Per-case evaluation result response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evaluation_id: uuid.UUID
    case_name: str
    task: str
    status: EvaluationResultStatus
    run_id: uuid.UUID | None
    tool_call_id: uuid.UUID | None
    expected_tool_name: str | None
    actual_tool_name: str | None
    output: dict[str, Any] | None
    error_message: str | None
    latency_ms: int | None
    token_count: int | None
    estimated_cost: Decimal | None = Field(default=None)
    trace_id: str | None
    created_at: datetime
    updated_at: datetime


class EvaluationRead(BaseModel):
    """Evaluation summary response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_version_id: uuid.UUID
    suite_name: str
    status: EvaluationStatus
    trace_id: str | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    total_cases: int | None
    passed_cases: int | None
    failed_cases: int | None
    success_rate: Decimal | None = Field(default=None)
    tool_accuracy: Decimal | None = Field(default=None)
    average_latency_ms: int | None
    total_cost: Decimal | None = Field(default=None)
    failure_rate: Decimal | None = Field(default=None)
    created_at: datetime
    updated_at: datetime


class EvaluationReportRead(BaseModel):
    """Detailed evaluation report response."""

    evaluation: EvaluationRead
    suite: EvaluationSuiteDefinition
    results: list[EvaluationResultRead]
    report: dict[str, Any]


class EvaluationMetricDeltaRead(BaseModel):
    """Metric comparison between two evaluations."""

    metric: str
    base_value: Decimal | int | None
    candidate_value: Decimal | int | None
    delta: Decimal | int | None


class EvaluationFindingRead(BaseModel):
    """Regression or improvement finding."""

    metric: str
    base_value: Decimal | int | None
    candidate_value: Decimal | int | None
    delta: Decimal | int | None
    reason: str


class EvaluationComparisonRead(BaseModel):
    """Comparison report for two agent versions."""

    base_evaluation: EvaluationRead
    candidate_evaluation: EvaluationRead
    metric_deltas: list[EvaluationMetricDeltaRead]
    regressions: list[EvaluationFindingRead]
    improvements: list[EvaluationFindingRead]
