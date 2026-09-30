from datetime import datetime, timezone
from uuid import uuid4


_HISTORY = []


def record_tool_run(result):
    entry = {
        "id": str(uuid4()),
        "tool": result.get("tool", "scan"),
        "target": result.get("target", ""),
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": result.get("status", "unknown"),
        "result": result,
    }
    _HISTORY.append(entry)
    del _HISTORY[:-100]
    return entry


def get_tool_history():
    return list(_HISTORY)


def delete_tool_run(run_id):
    before = len(_HISTORY)
    _HISTORY[:] = [item for item in _HISTORY if item["id"] != run_id]
    return len(_HISTORY) < before