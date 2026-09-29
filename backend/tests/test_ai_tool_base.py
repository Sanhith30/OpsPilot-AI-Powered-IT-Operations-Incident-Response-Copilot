from pydantic import BaseModel

from app.ai.tools.base import BaseTool


class TestToolInput(BaseModel):
    __test__ = False
    message: str


class TestTool(BaseTool):
    __test__ = False
    name = "test_tool"
    description = "A simple test tool."
    args_schema = TestToolInput

    def execute(self, validated_input: TestToolInput):
        return {
            "echo": validated_input.message,
        }


def test_base_tool_success():
    tool = TestTool()

    result = tool.run(
        {
            "message": "hello",
        }
    )

    assert result.tool_name == "test_tool"
    assert result.status == "SUCCESS"
    assert result.data["echo"] == "hello"
    assert result.execution_time_ms is not None


def test_base_tool_invalid_input():
    tool = TestTool()

    result = tool.run(
        {
            "wrong_field": "hello",
        }
    )

    assert result.tool_name == "test_tool"
    assert result.status == "FAILED"
    assert result.error_code == "INVALID_INPUT"


def test_base_tool_timeout():
    class TimeoutTestTool(BaseTool):
        name = "timeout_test_tool"
        description = "A timeout test tool."
        args_schema = TestToolInput

        def execute(self, validated_input):
            raise TimeoutError()

    tool = TimeoutTestTool()

    result = tool.run(
        {
            "message": "hello",
        }
    )

    assert result.tool_name == "timeout_test_tool"
    assert result.status == "TIMEOUT"
    assert result.error_code == "TOOL_TIMEOUT"