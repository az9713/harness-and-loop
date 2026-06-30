from __future__ import annotations

from .config import HarnessConfig
from .types import Action


class PermissionPolicy:
    def __init__(self, config: HarnessConfig) -> None:
        self.allowed_tools = set(config.allowed_tools)

    def authorize(self, action: Action) -> tuple[bool, str]:
        if action.kind != "tool":
            return True, "not a tool action"
        if action.name not in self.allowed_tools:
            return False, f"tool not allow-listed: {action.name}"
        if action.args.get("irreversible") is True:
            return False, "irreversible action requires explicit approval"
        return True, "allowed"

