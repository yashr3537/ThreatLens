import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1


def app_data_directory():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "ThreatLens"
    return Path.home() / "AppData" / "Local" / "ThreatLens"


def scans_directory(root=None):
    return Path(root) / "scans" if root is not None else app_data_directory() / "scans"


def load_scans(root=None):
    directory = scans_directory(root)
    if not directory.is_dir():
        return []

    scans = []
    for path in directory.glob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("schema_version") != SCHEMA_VERSION:
                continue
            scan = document.get("scan")
            if not isinstance(scan, dict) or not scan.get("success"):
                continue
            session = scan.setdefault("_session", {})
            session.setdefault("scan_id", document.get("scan_id", path.stem))
            session.setdefault("saved_at", document.get("saved_at", ""))
            scans.append(scan)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue

    scans.sort(
        key=lambda scan: scan.get("_session", {}).get("started_at", ""),
    )
    return scans


def save_scan(scan, root=None):
    if not isinstance(scan, dict) or not scan.get("success"):
        raise ValueError("Only successful scanner results can be saved.")

    session = scan.setdefault("_session", {})
    scan_id = session.get("scan_id") or str(uuid.uuid4())
    scan_id = str(uuid.UUID(scan_id))
    session["scan_id"] = scan_id
    session.setdefault("saved_at", datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"))

    directory = scans_directory(root)
    directory.mkdir(parents=True, exist_ok=True)
    document = {
        "schema_version": SCHEMA_VERSION,
        "scan_id": scan_id,
        "saved_at": session["saved_at"],
        "scan": scan,
    }

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=directory,
        prefix=f".{scan_id}.",
        suffix=".tmp",
        delete=False,
    )
    temporary_path = Path(handle.name)
    try:
        with handle:
            json.dump(document, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        destination = directory / f"{scan_id}.json"
        os.replace(temporary_path, destination)
        return destination
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def delete_scan(scan_id, root=None):
    try:
        normalized_id = str(uuid.UUID(scan_id))
    except (ValueError, TypeError, AttributeError):
        return False

    path = scans_directory(root) / f"{normalized_id}.json"
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False