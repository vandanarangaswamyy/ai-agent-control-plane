from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from app.domain.errors import BusinessRuleViolationError, NotFoundError
from app.schemas.evaluations import EvaluationSuiteDefinition


class EvaluationSuiteLoader:
    """Load and validate evaluation suite definitions from disk."""

    def __init__(self, suites_dir: Path | None = None) -> None:
        self._suites_dir = suites_dir or Path(__file__).resolve().parents[3] / "evals" / "suites"

    def load_suite(self, suite_name: str) -> EvaluationSuiteDefinition:
        suite_path = self._suites_dir / f"{suite_name}.json"
        if not suite_path.exists():
            raise NotFoundError(f"evaluation suite not found: {suite_name}")

        try:
            return EvaluationSuiteDefinition.model_validate_json(suite_path.read_text())
        except ValidationError as exc:
            raise BusinessRuleViolationError(
                f"invalid evaluation suite schema: {suite_name}"
            ) from exc
        except OSError as exc:
            raise BusinessRuleViolationError(
                f"unable to read evaluation suite: {suite_name}"
            ) from exc

    def list_suites(self) -> list[str]:
        if not self._suites_dir.exists():
            return []
        return sorted(path.stem for path in self._suites_dir.glob("*.json"))
