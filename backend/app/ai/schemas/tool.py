from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """
    Standard response returned by every OpsPilot AI tool.
    """

    tool_name: str = Field(
        ...,
        description="Unique name of the tool that produced the result.",
    )

    status: Literal[
        "SUCCESS",
        "FAILED",
        "TIMEOUT",
    ] = Field(
        ...,
        description="Execution status of the tool.",
    )

    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured result produced by the tool.",
    )

    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code when execution fails.",
    )

    error_message: str | None = Field(
        default=None,
        description="Human-readable error message when execution fails.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata.",
    )

    execution_time_ms: int | None = Field(
        default=None,
        ge=0,
        description="Tool execution time in milliseconds.",
    )