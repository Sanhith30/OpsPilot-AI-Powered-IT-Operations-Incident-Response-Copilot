from app.ai.schemas.tool import ToolResult


def test_tool_result_success():
    result = ToolResult(
        tool_name="test_tool",
        status="SUCCESS",
        data={
            "message": "hello",
        },
        metadata={
            "source": "test",
        },
        execution_time_ms=10,
    )

    assert result.tool_name == "test_tool"
    assert result.status == "SUCCESS"
    assert result.data["message"] == "hello"
    assert result.metadata["source"] == "test"
    assert result.execution_time_ms == 10


def test_tool_result_failure():
    result = ToolResult(
        tool_name="test_tool",
        status="FAILED",
        error_code="TEST_ERROR",
        error_message="Test tool failed.",
    )

    assert result.status == "FAILED"
    assert result.error_code == "TEST_ERROR"
    assert result.error_message == "Test tool failed."