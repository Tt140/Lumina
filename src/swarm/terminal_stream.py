"""LuminaLab Swarm - Real-time Hackathon Live Stream Handler.

Streams reasoning thoughts, tool calls, and generated tokens live to stdout
for Hackathon jury evaluation, while filtering any Arabic characters from the display.
"""

import re
import sys
from typing import Any

ARABIC_PATTERN = re.compile(r"[\u0600-\u06FF]")


class HackathonLiveStreamHandler:
    """Live streaming callback handler for Hackathon terminal demonstration."""

    def __init__(self, agent_label: str = "Agent", verbose_tool_use: bool = True) -> None:
        self.agent_label = agent_label
        self.tool_count = 0
        self._verbose_tool_use = verbose_tool_use

    def _sanitize(self, text: str) -> str:
        """Strip Arabic characters from the terminal stream."""
        if not text:
            return ""
        return ARABIC_PATTERN.sub("", str(text))

    def __call__(self, **kwargs: Any) -> None:
        reasoning_text = kwargs.get("reasoningText", False)
        data = kwargs.get("data", "")
        complete = kwargs.get("complete", False)
        tool_use = kwargs.get("event", {}).get("contentBlockStart", {}).get("start", {}).get("toolUse")

        if reasoning_text:
            clean_reasoning = self._sanitize(str(reasoning_text))
            if clean_reasoning:
                sys.stdout.write(clean_reasoning)
                sys.stdout.flush()

        if tool_use:
            self.tool_count += 1
            if self._verbose_tool_use:
                tool_name = tool_use.get("name", "tool")
                sys.stdout.write(f"\n[Tool #{self.tool_count}]: {tool_name}\n")
                sys.stdout.flush()

        if data:
            clean_data = self._sanitize(str(data))
            if clean_data:
                sys.stdout.write(clean_data)
                if complete:
                    sys.stdout.write("\n")
                sys.stdout.flush()

        if complete and data:
            sys.stdout.write("\n")
            sys.stdout.flush()


def get_hackathon_callback_handler(agent_label: str = "Agent") -> HackathonLiveStreamHandler:
    """Instantiate a Hackathon live stream callback handler for an agent."""
    return HackathonLiveStreamHandler(agent_label=agent_label)
