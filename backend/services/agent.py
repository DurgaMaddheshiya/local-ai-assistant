"""
Agent service — future tool-calling architecture (stub).
The AI cannot call tools directly; every execution is gated through
the ToolRegistry which validates permissions and requires confirmation
for dangerous operations.
"""
import logging
from typing import Any, Dict, List, Optional
from ..tools.registry import tool_registry, PermissionLevel

logger = logging.getLogger(__name__)


class AgentService:
    """
    Coordinates LLM responses with optional tool execution.

    Current state: stub — returns tool availability information only.
    Full implementation (parse tool calls from LLM output, execute,
    feed result back) will be added in a future release.
    """

    def get_available_tools_summary(self) -> List[Dict]:
        """Return a list of enabled tools the agent may use"""
        return tool_registry.list_tools(enabled_only=True)

    def get_all_tools_summary(self) -> List[Dict]:
        """Return all registered tools (enabled and disabled)"""
        return tool_registry.list_tools(enabled_only=False)

    def enable_tool(self, tool_name: str) -> bool:
        return tool_registry.enable_tool(tool_name)

    def disable_tool(self, tool_name: str) -> bool:
        return tool_registry.disable_tool(tool_name)

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool through the registry's safety layer.
        The registry will reject disabled tools and tools requiring confirmation.
        """
        logger.info(f"Agent tool request: {tool_name}")
        return tool_registry.execute_tool(tool_name, params)

    def build_tool_context(self) -> Optional[str]:
        """
        Build a context string describing available tools for the system prompt.
        Returns None if no tools are enabled.
        """
        enabled = self.get_available_tools_summary()
        if not enabled:
            return None

        lines = ["Available tools:"]
        for tool in enabled:
            lines.append(f"  - {tool['name']}: {tool['description']}")

        return "\n".join(lines)
