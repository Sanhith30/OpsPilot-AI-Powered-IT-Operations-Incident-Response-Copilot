from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, ClassVar

from pydantic import BaseModel, ValidationError

from app.ai.schemas.tool import ToolResult
from app.observability.metrics import AI_TOOL_CALLS_TOTAL


class BaseTool(ABC):
    """
    Base interface for all OpsPilot AI tools.

    Every tool must:
    1. Have a unique name.
    2. Have a clear description.
    3. Define an input schema.
    4. Implement the actual execution logic.
    5. Return a standardized ToolResult through run().
    """

    name: ClassVar[str]
    description: ClassVar[str]
    args_schema: ClassVar[type[BaseModel]]

    def run(self, raw_input: dict[str, Any]) -> ToolResult:
        """
        Validate input, execute the tool, and return a standardized result.
        """

        start_time = perf_counter()

        try:
            validated_input = self.args_schema.model_validate(raw_input)
            result = self.execute(validated_input)
            execution_time_ms = int(
                (perf_counter() - start_time) * 1000
            )

            tool_result = ToolResult(
                tool_name=self.name,
                status="SUCCESS",
                data=result,
                execution_time_ms=execution_time_ms,
            )

        except ValidationError as exc:
            execution_time_ms = int(
                (perf_counter() - start_time) * 1000
            )

            tool_result = ToolResult(
                tool_name=self.name,
                status="FAILED",
                error_code="INVALID_INPUT",
                error_message="Invalid input provided to the tool.",
                metadata={
                    "validation_errors": exc.errors(),
                },
                execution_time_ms=execution_time_ms,
            )

        except TimeoutError:
            execution_time_ms = int(
                (perf_counter() - start_time) * 1000
            )

            tool_result = ToolResult(
                tool_name=self.name,
                status="TIMEOUT",
                error_code="TOOL_TIMEOUT",
                error_message="Tool execution timed out.",
                execution_time_ms=execution_time_ms,
            )

        except Exception:
            execution_time_ms = int(
                (perf_counter() - start_time) * 1000
            )

            tool_result = ToolResult(
                tool_name=self.name,
                status="FAILED",
                error_code="TOOL_EXECUTION_ERROR",
                error_message="Tool execution failed.",
                execution_time_ms=execution_time_ms,
            )

        AI_TOOL_CALLS_TOTAL.labels(
            tool_name=tool_result.tool_name,
            status=tool_result.status,
        ).inc()

        return tool_result

    @abstractmethod
    def execute(self, validated_input: BaseModel) -> dict[str, Any]:
        """
        Execute the actual tool logic.

        Subclasses implement this method.
        """
        raise NotImplementedError