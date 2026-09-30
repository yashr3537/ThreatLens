from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class ToolResult:
    tool: str
    target: str
    status: str
    data: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"))

    def to_dict(self):
        return asdict(self)