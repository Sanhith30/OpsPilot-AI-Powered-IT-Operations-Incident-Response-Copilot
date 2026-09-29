from typing import Any

from app.ai.schemas.tool import ToolResult
from app.ai.tools.base import BaseTool


class ToolRegistry:
    """
    Central registry for all OpsPilot AI tools.

    The registry is responsible for:
    - registering tools
    - preventing duplicate tool names
    - retrieving tools by name
    - listing available tools
    - executing a tool by name
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool using its unique tool name.
        """

        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered."
            )

        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> BaseTool:
        """
        Retrieve a registered tool by name.
        """

        tool = self._tools.get(tool_name)

        if tool is None:
            raise KeyError(
                f"Tool '{tool_name}' is not registered."
            )

        return tool

    def list_tools(self) -> list[dict[str, str]]:
        """
        Return basic information about all registered tools.
        """

        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self._tools.values()
        ]

    def execute(
        self,
        tool_name: str,
        raw_input: dict[str, Any],
    ) -> ToolResult:
        """
        Execute a registered tool using its name.
        """

        tool = self.get(tool_name)

        return tool.run(raw_input)