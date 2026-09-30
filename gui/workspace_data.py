import json

from .pages.scan_url import get_report_history
from .pages.scan_url import get_session_tool_history


_manual_targets = []
_target_metadata = {}
_deleted_targets = set()
_finding_overrides = {}
_settings = {
    "startup_page": "dashboard",
    "notifications": True,
    "auto_save": True,
    "confirm_delete": True,
    "timeout": "500",
    "concurrency": "8",
    "port_range": "common",
    "scan_speed": "Conservative",
    "wordlist": "",
    "default_format": "PDF",
    "theme": "Dark",
    "accent": "#28D8C5",
    "compact": False,
    "animations": True,
    "modules": {"DNS": True, "Subdomain": True, "Host": True, "Port": True},
}
_read_notifications = set()
_cleared_notifications = set()


def _scan_key(report):
    session = report.get("_session", {})
    return f"{report.get('target', {}).get('hostname', '')}:{session.get('started_at', '')}"


def _real_target(report):
    target = report.get("target", {})
    hostname = target.get("hostname", "")
    addresses = {
        address
        for host in report.get("hosts", [])
        for address in host.get("addresses", [])
    }
    metadata = _target_metadata.get(hostname.lower(), {})
    return {
        "id": f"scan:{hostname.lower()}",
        "target": hostname,
        "type": "URL / domain",
        "status": "Completed",
        "assets": len(addresses),
        "findings": None,
        "last_scan": report.get("_session", {}).get("started_at", ""),
        "tags": list(metadata.get("tags", [])),
        "notes": metadata.get("notes", ""),
        "report": report,
    }


def get_all_targets():
    by_hostname = {}
    for report in get_report_history():
        target = _real_target(report)
        key = target["target"].lower()
        if key and key not in _deleted_targets:
            by_hostname[key] = target
    for target in _manual_targets:
        if target["target"].lower() not in _deleted_targets:
            by_hostname.setdefault(target["target"].lower(), target)
    return list(by_hostname.values())


def add_target(target_name, target_type="URL / domain", tags=None, notes=""):
    name = (target_name or "").strip()
    if not name:
        return None
    target = {
        "id": f"manual:{name.lower()}",
        "target": name,
        "type": target_type,
        "status": "Added",
        "assets": None,
        "findings": None,
        "last_scan": "Not scanned",
        "tags": list(tags or []),
        "notes": notes or "",
    }
    existing = next((item for item in _manual_targets if item["target"].lower() == name.lower()), None)
    if existing:
        existing.update(target)
        return existing
    _manual_targets.insert(0, target)
    _deleted_targets.discard(name.lower())
    return target


def delete_target(target_id):
    hostname = target_id.split(":", 1)[-1].lower()
    _deleted_targets.add(hostname)
    _manual_targets[:] = [item for item in _manual_targets if item["target"].lower() != hostname]


def update_target_tags(target_id, tags):
    hostname = target_id.split(":", 1)[-1].lower()
    _target_metadata.setdefault(hostname, {})["tags"] = list(tags)
    for target in _manual_targets:
        if target["target"].lower() == hostname:
            target["tags"] = list(tags)


def update_target_notes(target_id, notes):
    hostname = target_id.split(":", 1)[-1].lower()
    _target_metadata.setdefault(hostname, {})["notes"] = notes
    for target in _manual_targets:
        if target["target"].lower() == hostname:
            target["notes"] = notes


def get_all_findings(severity=None, category=None, target=None, status=None, search=None):
    findings = []
    if search:
        query = search.lower()
        findings = [item for item in findings if query in json.dumps(item).lower()]
    return findings


def update_finding_status(finding_id, new_status):
    _finding_overrides.setdefault(finding_id, {})["status"] = new_status


def update_finding_notes(finding_id, notes):
    _finding_overrides.setdefault(finding_id, {})["notes"] = notes


def get_all_endpoints(method=None, endpoint_type=None, search=None):
    return []


def get_all_technologies(category=None, search=None):
    return []


def get_all_network(protocol=None, state=None, search=None):
    network = []
    unique = set()
    for report in get_report_history():
        for port in report.get("ports", []):
            key = (port.get("address"), port.get("port"), port.get("protocol"))
            if key in unique:
                continue
            unique.add(key)
            network.append({
                "host": port.get("hostname", ""),
                "address": port.get("address", ""),
                "port": str(port.get("port", "")),
                "protocol": port.get("protocol", ""),
                "state": port.get("state", ""),
                "service": port.get("service", ""),
                "version": port.get("version", ""),
            })
    if protocol and protocol != "All":
        network = [item for item in network if item["protocol"].lower() == protocol.lower()]
    if state and state != "All":
        network = [item for item in network if item["state"].lower() == state.lower()]
    if search:
        query = search.lower()
        network = [item for item in network if query in json.dumps(item).lower()]
    return network


def get_all_evidence(evidence_type=None, target=None, search=None):
    evidence = []
    for report in get_report_history():
        hostname = report.get("target", {}).get("hostname", "")
        captured = report.get("_session", {}).get("started_at", "")
        dns = report.get("dns", {})
        if dns.get("addresses"):
            evidence.append({
                "id": f"dns:{_scan_key(report)}",
                "type": "DNS Result",
                "name": f"DNS resolution · {hostname}",
                "target": hostname,
                "captured": captured,
                "size": "",
                "content": json.dumps(dns, indent=2),
            })
        for port in report.get("ports", []):
            evidence.append({
                "id": f"port:{_scan_key(report)}:{port.get('address')}:{port.get('port')}",
                "type": "Port Result",
                "name": f"{port.get('port')}/{port.get('protocol')} · {port.get('service')}",
                "target": hostname,
                "captured": captured,
                "size": "",
                "content": json.dumps(port, indent=2),
            })
    if evidence_type and evidence_type != "All":
        evidence = [item for item in evidence if item["type"].lower() == evidence_type.lower()]
    if target and target != "All":
        evidence = [item for item in evidence if item["target"].lower() == target.lower()]
    if search:
        query = search.lower()
        evidence = [item for item in evidence if query in json.dumps(item).lower()]
    return evidence


def get_all_history():
    history = []
    for report in reversed(get_report_history()):
        session = report.get("_session", {})
        history.append({
            "id": f"history:{_scan_key(report)}",
            "target": report.get("target", {}).get("hostname", ""),
            "scan_type": session.get("scan_profile", "TCP"),
            "start_time": session.get("started_at", ""),
            "duration": f"{session.get('duration_seconds', 0)} s",
            "status": "Completed",
            "findings": None,
            "report": report,
        })
    return history


def get_all_reports():
    reports = []
    for report in reversed(get_report_history()):
        session = report.get("_session", {})
        hostname = report.get("target", {}).get("hostname", "")
        reports.append({
            "id": f"report:{_scan_key(report)}",
            "name": f"ThreatLens-{hostname}-{session.get('started_at', '')[:10]}",
            "target": hostname,
            "scan_date": session.get("started_at", ""),
            "findings": None,
            "status": "Completed",
            "format": "JSON",
            "report": report,
        })
    for entry in reversed(get_session_tool_history()):
        hostname = entry.get("result", {}).get("target", "")
        reports.insert(0, {
            "id": f"tool-report:{entry['id']}",
            "name": f"Tool-{entry.get('tool', 'result')}-{hostname}-{entry.get('timestamp', '')[:10]}",
            "target": hostname,
            "scan_date": entry.get("timestamp", ""),
            "findings": None,
            "status": entry.get("status", "unknown"),
            "format": "JSON",
            "report": entry.get("result", {}),
            "history_kind": "tool",
        })
    return reports


def get_all_notifications():
    notifications = []
    for report in reversed(get_report_history()):
        key = _scan_key(report)
        if key in _cleared_notifications:
            continue
        notifications.append({
            "id": key,
            "title": "Phase 1 scan completed",
            "detail": report.get("target", {}).get("hostname", ""),
            "when": report.get("_session", {}).get("started_at", ""),
            "category": "Info",
            "read": key in _read_notifications,
        })
    return notifications


def mark_all_notifications_read():
    _read_notifications.update(item["id"] for item in get_all_notifications())


def clear_notifications():
    _cleared_notifications.update(item["id"] for item in get_all_notifications())


def get_settings():
    return _settings


def update_settings(updates):
    _settings.update(updates)


def search_all_data(query):
    query = (query or "").strip().lower()
    if not query:
        return {}
    results = {}
    for category, rows, page_id, get_title in [
        ("Targets", get_all_targets(), "targets", lambda row: row["target"]),
        ("Network Ports", get_all_network(), "network", lambda row: f"{row['port']}/{row['protocol']} {row['service']}"),
        ("Reports", get_all_reports(), "reports", lambda row: row["name"]),
    ]:
        matches = []
        for row in rows:
            if query in json.dumps(row, default=str).lower():
                matches.append({
                    "title": get_title(row),
                    "subtitle": category,
                    "page": page_id,
                })
        if matches:
            results[category] = matches
    return results