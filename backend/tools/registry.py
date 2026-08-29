"""
Tool registry for future agent capabilities.
Provides a safe, controlled architecture for AI tool execution.
"""
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for tools"""
    READ_ONLY = "read_only"         # Safe reads — no side effects
    WRITE = "write"                 # Creates or modifies data
    SYSTEM = "system"               # Modifies OS/filesystem
    DANGEROUS = "dangerous"         # Requires explicit user confirmation


@dataclass
class ToolSchema:
    """JSON schema definition for a tool's input parameters"""
    type: str = "object"
    properties: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)


@dataclass
class Tool:
    """Represents a single registered tool"""
    name: str
    description: str
    permission_level: PermissionLevel
    input_schema: ToolSchema
    execute: Callable
    enabled: bool = False           # Tools are DISABLED by default — must be opted in
    requires_confirmation: bool = False

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "permission_level": self.permission_level.value,
            "enabled": self.enabled,
            "requires_confirmation": self.requires_confirmation,
            "input_schema": {
                "type": self.input_schema.type,
                "properties": self.input_schema.properties,
                "required": self.input_schema.required
            }
        }


class ToolRegistry:
    """
    Central registry for all AI tools.

    Design principles:
    - All tools are DISABLED by default.
    - DANGEROUS tools always require user confirmation.
    - The AI cannot invoke tools directly — the registry validates every call.
    - Execution is always logged.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_builtin_tools()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry"""
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered — overwriting")
        self._tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name} (enabled={tool.enabled})")

    def _register_builtin_tools(self) -> None:
        """Register the built-in stub tools for future implementation"""

        # --- File system tools (READ) ---
        self.register(Tool(
            name="read_file",
            description="Read the contents of a local text file",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema=ToolSchema(
                properties={
                    "path": {"type": "string", "description": "Absolute or relative file path"},
                    "encoding": {"type": "string", "default": "utf-8"}
                },
                required=["path"]
            ),
            execute=self._stub_execute,
            enabled=False
        ))

        self.register(Tool(
            name="list_directory",
            description="List files and directories at a given path",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema=ToolSchema(
                properties={
                    "path": {"type": "string", "description": "Directory path to list"},
                    "recursive": {"type": "boolean", "default": False}
                },
                required=["path"]
            ),
            execute=self._stub_execute,
            enabled=False
        ))

        self.register(Tool(
            name="search_files",
            description="Search for files matching a pattern in a directory",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema=ToolSchema(
                properties={
                    "path": {"type": "string", "description": "Directory to search in"},
                    "pattern": {"type": "string", "description": "Glob or regex pattern"},
                    "content_search": {"type": "string", "description": "Optional text to search inside files"}
                },
                required=["path", "pattern"]
            ),
            execute=self._stub_execute,
            enabled=False
        ))

        # --- File system tools (WRITE) ---
        self.register(Tool(
            name="write_file",
            description="Write text content to a local file",
            permission_level=PermissionLevel.WRITE,
            input_schema=ToolSchema(
                properties={
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "overwrite": {"type": "boolean", "default": False}
                },
                required=["path", "content"]
            ),
            execute=self._stub_execute,
            enabled=False,
            requires_confirmation=True
        ))

        self.register(Tool(
            name="create_directory",
            description="Create a new directory",
            permission_level=PermissionLevel.WRITE,
            input_schema=ToolSchema(
                properties={
                    "path": {"type": "string"},
                    "parents": {"type": "boolean", "default": True}
                },
                required=["path"]
            ),
            execute=self._stub_execute,
            enabled=False,
            requires_confirmation=True
        ))

        # --- Command execution (DANGEROUS — never auto-enabled) ---
        self.register(Tool(
            name="run_command",
            description="Execute a shell command (PowerShell/CMD). NEVER enabled by default.",
            permission_level=PermissionLevel.DANGEROUS,
            input_schema=ToolSchema(
                properties={
                    "command": {"type": "string", "description": "Command to execute"},
                    "working_directory": {"type": "string"},
                    "timeout_seconds": {"type": "integer", "default": 30}
                },
                required=["command"]
            ),
            execute=self._stub_execute,
            enabled=False,
            requires_confirmation=True
        ))

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a registered tool with safety validation.
        Returns a result dict with 'success', 'result', and optional 'error'.
        """
        tool = self._tools.get(name)

        if not tool:
            logger.warning(f"Unknown tool requested: {name}")
            return {"success": False, "error": f"Tool '{name}' does not exist"}

        if not tool.enabled:
            logger.warning(f"Disabled tool requested: {name}")
            return {
                "success": False,
                "error": f"Tool '{name}' is not enabled. Enable it in settings first."
            }

        if tool.requires_confirmation:
            # Caller must handle confirmation before reaching here
            logger.info(f"Tool '{name}' requires user confirmation")
            return {
                "success": False,
                "requires_confirmation": True,
                "tool_name": name,
                "params": params,
                "message": f"Tool '{name}' requires explicit user approval before execution."
            }

        # Validate required parameters
        missing = [p for p in tool.input_schema.required if p not in params]
        if missing:
            return {
                "success": False,
                "error": f"Missing required parameters: {', '.join(missing)}"
            }

        # Execute
        logger.info(f"Executing tool: {name} | params={list(params.keys())}")
        try:
            result = tool.execute(name, params)
            logger.info(f"Tool '{name}' completed successfully")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool '{name}' execution error: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Enable / disable
    # ------------------------------------------------------------------

    def enable_tool(self, name: str) -> bool:
        tool = self._tools.get(name)
        if not tool:
            return False
        tool.enabled = True
        logger.info(f"Tool enabled: {name}")
        return True

    def disable_tool(self, name: str) -> bool:
        tool = self._tools.get(name)
        if not tool:
            return False
        tool.enabled = False
        logger.info(f"Tool disabled: {name}")
        return True

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self, enabled_only: bool = False) -> List[Dict]:
        tools = self._tools.values()
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        return [t.to_dict() for t in tools]

    def get_enabled_tools(self) -> List[Tool]:
        return [t for t in self._tools.values() if t.enabled]

    def get_tools_by_permission(self, level: PermissionLevel) -> List[Tool]:
        return [t for t in self._tools.values() if t.permission_level == level]

    # ------------------------------------------------------------------
    # Stub
    # ------------------------------------------------------------------

    @staticmethod
    def _stub_execute(tool_name: str, params: Dict[str, Any]) -> Any:
        """Placeholder — replaced when a tool is fully implemented"""
        return {
            "status": "not_implemented",
            "message": f"Tool '{tool_name}' is defined but not yet implemented.",
            "params_received": list(params.keys())
        }


# Module-level singleton
tool_registry = ToolRegistry()
