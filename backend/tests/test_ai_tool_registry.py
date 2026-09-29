from pydantic import BaseModel

from app.ai.tools.base import BaseTool
from app.ai.tools.registry import ToolRegistry


class EchoInput(BaseModel):
    message: str


class EchoTool(BaseTool):
    name = "echo"
    description = "Echo a message."
    args_schema = EchoInput

    def execute(self, validated_input: EchoInput):
        return {
            "echo": validated_input.message,
        }


def test_register_and_get_tool():
    registry = ToolRegistry()
    tool = EchoTool()

    registry.register(tool)

    retrieved = registry.get("echo")

    assert retrieved is tool


def test_execute_registered_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())

    result = registry.execute(
        "echo",
        {
            "message": "hello",
        },
    )

    assert result.tool_name == "echo"
    assert result.status == "SUCCESS"
    assert result.data["echo"] == "hello"


def test_duplicate_tool_registration_fails():
    registry = ToolRegistry()

    registry.register(EchoTool())

    try:
        registry.register(EchoTool())
        assert False, "Expected duplicate registration to fail."
    except ValueError as exc:
        assert "already registered" in str(exc)