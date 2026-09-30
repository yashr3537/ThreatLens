import flet as ft

from components import COLORS, empty_state, page_heading, panel, show_notice, status_badge
from nav_items import PAGE_LABELS
from .scan_url import get_latest_report, get_report_history


TABLE_SPECS = {
    "targets": ("Targets", "Authorized targets from completed scans.", ["Target", "Type", "DNS status", "Assets", "Last scan"]),
    "assets": ("Assets", "Hosts and addresses returned by the scanner.", ["Host", "Address", "Resolution", "Source"]),
    "findings": ("Findings", "Finding analysis is not part of the connected Phase 1 scanner.", ["Severity", "Title", "Target", "Category", "Status"]),
    "endpoints": ("Endpoints", "Endpoint discovery is not connected to the current scanner.", ["URL", "Method", "Status", "Type", "Parameters", "Source"]),
    "technologies": ("Technologies", "Technology detection is not connected to the current scanner.", ["Technology", "Category", "Confidence", "Evidence"]),
    "network": ("Network inventory", "TCP ports and services returned by completed scans.", ["Host", "Address", "Port", "Protocol", "State", "Service", "Version"]),
    "web_intelligence": ("Web intelligence", "Web crawling and application analysis are not connected.", ["URL", "Method", "Status", "Type", "Source"]),
    "evidence": ("Evidence", "The scanner does not currently persist evidence artifacts.", ["Type", "Name", "Target", "Captured", "Size"]),
    "scan_history": ("Scan history", "Completed scans recorded during this application session.", ["Target", "Scan type", "Started", "Duration", "Status"]),
    "reports": ("Reports", "Scanner reports recorded during this application session.", ["Report", "Target", "Scan date", "Findings", "Format"]),
}

FILTER_SPECS = {
    "targets": [("Type", ["Domain", "URL / domain"]), ("DNS status", ["resolved", "not resolved", "timeout", "error"])],
    "findings": [("Severity", ["Critical", "High", "Medium", "Low", "Info"]), ("Category", ["Network", "DNS", "TLS", "Headers", "Cookies", "Web"]) , ("Target", []), ("Status", ["Open", "Review", "Reviewed", "Accepted"])],
    "endpoints": [("Method", ["GET", "POST", "PUT", "DELETE"]), ("Type", ["API", "Static", "Dynamic"])],
    "network": [("Protocol", ["TCP", "UDP"]), ("State", ["Open", "Closed", "Filtered"])],
    "technologies": [("Category", ["Server", "Framework", "JavaScript", "Database", "CDN", "Hosting", "CMS"])],
    "reports": [("Format", ["JSON", "TXT", "HTML", "PDF"])],
    "evidence": [("Type", ["Screenshot", "HTTP Response", "Headers", "DNS Result", "Port Result", "Endpoint", "Technology"])],
}


def _session_label(report):
    return report.get("_session", {}).get("started_at", "Time unavailable")


def _records(page_id):
    history = get_report_history()
    if page_id == "targets":
        records = {}
        for report in history:
            target = report["target"]
            key = target["hostname"].lower()
            hosts = report.get("hosts", [])
            record = {
                "Target": target["hostname"],
                "Type": "URL / domain",
                "DNS status": report.get("dns", {}).get("status", "unknown"),
                "Assets": str(sum(len(host.get("addresses", [])) for host in hosts)),
                "Last scan": _session_label(report),
            }
            current = records.get(key)
            if current is None or record["Last scan"] >= current["Last scan"]:
                records[key] = record
        return list(records.values())

    if page_id == "assets":
        found = {}
        for report in history:
            for host in report.get("hosts", []):
                for address in host.get("addresses", []):
                    key = (host.get("hostname", "").lower(), address.lower())
                    found[key] = {
                        "Host": host.get("hostname", ""),
                        "Address": address,
                        "Resolution": host.get("status", "unknown"),
                        "Source": "DNS inventory",
                    }
        return list(found.values())

    if page_id == "network":
        found = {}
        for report in history:
            for port in report.get("ports", []):
                key = (port.get("address"), port.get("port"), port.get("protocol"))
                found[key] = {
                    "Host": port.get("hostname", ""),
                    "Address": port.get("address", ""),
                    "Port": str(port.get("port", "")),
                    "Protocol": port.get("protocol", ""),
                    "State": port.get("state", ""),
                    "Service": port.get("service", ""),
                    "Version": port.get("version", ""),
                }
        return list(found.values())

    if page_id in ("scan_history", "reports"):
        records = []
        for report in reversed(history):
            target = report["target"]["hostname"]
            session = report.get("_session", {})
            if page_id == "scan_history":
                records.append({
                    "Target": target,
                    "Scan type": session.get("scan_profile", "TCP profile"),
                    "Started": session.get("started_at", ""),
                    "Duration": f"{session.get('duration_seconds', 0)} s",
                    "Status": "Completed",
                })
            else:
                records.append({
                    "Report": f"{target}-{session.get('started_at', 'scan')}",
                    "Target": target,
                    "Scan date": session.get("started_at", ""),
                    "Findings": "Not analyzed",
                    "Format": "JSON data",
                })
        return records

    return []


def _detail_dialog(page, heading, record):
    detail_rows = [
        ft.Row(
            [
                ft.Text(f"{key}", size=11, color=COLORS["muted"], width=115),
                ft.Text(str(value), size=12, color=COLORS["text"], selectable=True, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        for key, value in record.items()
    ]
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text(heading),
            content=ft.Container(content=ft.Column(detail_rows, tight=True, scroll=ft.ScrollMode.AUTO), width=480),
            actions=[ft.TextButton("Close", on_click=lambda event: page.pop_dialog())],
        )
    )


def _row_actions(page, page_id, title, record, open_page):
    if page_id == "targets":
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_HORIZ,
            tooltip="Target actions",
            items=[
                ft.PopupMenuItem(content="Open", on_click=lambda event: open_page("target_explorer")),
                ft.PopupMenuItem(content="Scan", on_click=lambda event: open_page("scan_center")),
                ft.PopupMenuItem(content="Rescan", on_click=lambda event: open_page("scan_center")),
                ft.PopupMenuItem(content="Rename", on_click=lambda event: show_notice(page, "Rename is a UI control; target storage is not connected.")),
                ft.PopupMenuItem(content="Delete", on_click=lambda event: show_notice(page, "Delete is disabled until persistent target storage is connected.")),
                ft.PopupMenuItem(content="Export", on_click=lambda event: show_notice(page, "Use Reports to export completed scanner results.")),
            ],
        )
    return ft.TextButton("View", on_click=lambda event: _detail_dialog(page, title, record))


def _table_page(page, page_id, open_page):
    title, description, columns = TABLE_SPECS[page_id]
    records = _records(page_id)
    search = ft.TextField(
        hint_text=f"Search {title.lower()}...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=270,
        dense=True,
    )
    filter_controls = []
    filter_fields = []
    for filter_name, options in FILTER_SPECS.get(page_id, []):
        if not options and records:
            options = sorted({str(row.get(filter_name, "")) for row in records if row.get(filter_name)})
        filter_fields.append(filter_name)
        filter_controls.append(
            ft.Dropdown(
                label=filter_name,
                value="All",
                width=145,
                dense=True,
                options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(value) for value in options],
            )
        )
    table_area = ft.Container(expand=True)
    record_count = ft.Text(size=10, color=COLORS["muted"])

    def render_rows(event=None):
        query = (search.value or "").strip().lower()
        filtered = [
            row for row in records
            if (not query or query in " ".join(str(value) for value in row.values()).lower())
            and all(control.value == "All" or not row.get(field) or row.get(field) == control.value for field, control in zip(filter_fields, filter_controls))
        ]
        record_count.value = f"{len(filtered)} records"
        if not filtered:
            explanation = description if not records else "No records match the current search or filter."
            table_area.content = empty_state(ft.Icons.INBOX_OUTLINED, "No data available", explanation)
        else:
            data_table = ft.DataTable(
                columns=[ft.DataColumn(ft.Text(column.upper(), size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)) for column in columns]
                + [ft.DataColumn(ft.Text("ACTIONS", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD))],
                rows=[
                    ft.DataRow(
                        cells=[ft.DataCell(ft.Text(str(row.get(column, "—")), size=11, color=COLORS["text"], selectable=True)) for column in columns]
                        + [ft.DataCell(_row_actions(page, page_id, title, row, open_page))],
                    )
                    for row in filtered
                ],
                column_spacing=18,
                horizontal_margin=10,
                heading_row_height=38,
                data_row_min_height=44,
                heading_row_color=COLORS["raised"],
                bgcolor=COLORS["panel"],
                border_radius=6,
            )
            table_area.content = ft.Row([data_table], scroll=ft.ScrollMode.AUTO)
        if event is not None:
            event.page.update()

    search.on_change = render_rows
    for control in filter_controls:
        control.on_change = render_rows
    render_rows()

    toolbar = ft.Row([search, *filter_controls, ft.Container(expand=True), record_count, ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh from current session", on_click=render_rows)], wrap=True)
    if page_id == "targets":
        toolbar.controls.insert(0, ft.Button("Add target", icon=ft.Icons.ADD, on_click=lambda event: open_page("scan_center")))
    if page_id == "findings":
        toolbar.controls.extend([
            ft.OutlinedButton("Mark reviewed", on_click=lambda event: show_notice(page, "Select a real finding after a finding provider is connected.")),
            ft.OutlinedButton("Add note", on_click=lambda event: show_notice(page, "Notes are unavailable until findings are provided.")),
            ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Export evidence", on_click=lambda event: show_notice(page, "No evidence is available to export.")),
        ])
    return ft.Container(
        expand=True,
        padding=24,
        content=ft.Column(
            [
                page_heading("Workspace", title, description),
                panel([toolbar, table_area], title="Current session inventory", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )


def _asset_graph(page):
    report = get_latest_report()
    nodes = []
    if report:
        target = report["target"]["hostname"]
        nodes.append((target, "DOMAIN", COLORS["accent"]))
        for subdomain in report.get("subdomain_discovery", {}).get("results", []):
            nodes.append((subdomain.get("hostname", ""), "SUBDOMAIN", COLORS["blue"]))
        for host in report.get("hosts", []):
            nodes.extend((address, "IP ADDRESS", COLORS["lime"]) for address in host.get("addresses", []))
        for port in report.get("ports", []):
            nodes.append((f"{port.get('port')}/{port.get('protocol')}", port.get("service", "PORT").upper(), COLORS["amber"]))
    graph_content = empty_state(ft.Icons.HUB, "No graph data available", "Run a real scan to build the graph from discovered domains, addresses, and ports.")
    if nodes:
        graph_content = ft.ResponsiveRow(
            [
                ft.Container(
                    content=ft.Column([ft.Text(kind, size=8, color=tone, weight=ft.FontWeight.BOLD), ft.Text(label, size=11, color=COLORS["text"], selectable=True)], spacing=4),
                    padding=12,
                    bgcolor=COLORS["panel"],
                    border=ft.Border.all(1, COLORS["line"]),
                    border_radius=6,
                    col={"xs": 12, "sm": 6, "lg": 3},
                )
                for label, kind, tone in nodes
            ],
            spacing=8,
            run_spacing=8,
        )
    return ft.Container(
        expand=True,
        padding=24,
        content=ft.Column(
            [
                page_heading("Targets", "Asset graph", "Relationships from real scanner data only."),
                ft.Row([
                    ft.TextField(hint_text="Search real nodes...", width=230, dense=True),
                    ft.Dropdown(label="Node type", value="All", width=150, dense=True, options=[ft.dropdown.Option(item) for item in ["All", "Domain", "Subdomain", "IP", "Port"]]),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.ZOOM_OUT, tooltip="Zoom out", on_click=lambda event: show_notice(event.page, "Zoom controls will be connected to the graph view.")),
                    ft.IconButton(ft.Icons.ZOOM_IN, tooltip="Zoom in", on_click=lambda event: show_notice(event.page, "Zoom controls will be connected to the graph view.")),
                    ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh", on_click=lambda event: show_notice(event.page, "Graph data is read from completed scans.")),
                    ft.IconButton(ft.Icons.FULLSCREEN, tooltip="Fullscreen", on_click=lambda event: show_notice(event.page, "Fullscreen graph view is not connected yet.")),
                ], wrap=True),
                panel([graph_content], title="Discovered relationships", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )


def _target_explorer(page, open_page):
    report = get_latest_report()
    section_picker = ft.Dropdown(
        label="Section",
        value="Overview",
        width=200,
        options=[ft.dropdown.Option(item) for item in ["Overview", "Domains", "Subdomains", "IP Addresses", "Ports", "Services", "URLs", "Endpoints", "APIs", "Technologies", "Findings"]],
    )
    details = ft.Container(expand=True)

    def render(event=None):
        if report is None:
            details.content = empty_state(ft.Icons.PUBLIC, "No target selected", "Targets appear here after a successful scanner run.")
        elif section_picker.value in ("Overview", "Domains"):
            target = report["target"]
            lines = [f"URL: {target['input']}", f"Hostname: {target['hostname']}", f"DNS status: {report['dns']['status']}"]
            details.content = panel([ft.Text(line, size=12, color=COLORS["text"]) for line in lines], title=section_picker.value)
        elif section_picker.value == "Subdomains":
            values = report.get("subdomain_discovery", {}).get("results", [])
            details.content = _simple_real_list("Subdomains", [f"{row['hostname']} · {', '.join(row['addresses'])}" for row in values])
        elif section_picker.value in ("IP Addresses", "Ports", "Services"):
            rows = report.get("hosts", []) if section_picker.value == "IP Addresses" else report.get("ports", [])
            lines = []
            for row in rows:
                if section_picker.value == "IP Addresses":
                    lines.extend(f"{row['hostname']} · {address}" for address in row.get("addresses", []))
                elif section_picker.value == "Ports":
                    lines.append(f"{row['address']} · {row['port']}/{row['protocol']} · {row['state']}")
                else:
                    lines.append(f"{row['port']} · {row['service']} · {row['version'] or 'version not detected'}")
            details.content = _simple_real_list(section_picker.value, lines)
        else:
            details.content = empty_state(ft.Icons.INBOX_OUTLINED, "No data available", f"{section_picker.value} are not included in the connected scanner output yet.")
        if event:
            event.page.update()

    section_picker.on_change = render
    render()
    return ft.Container(
        expand=True,
        padding=24,
        content=ft.Column(
            [
                page_heading("Targets", "Target explorer", "Inspect fields returned by the latest real scan."),
                ft.Row([ft.Text(report["target"]["hostname"] if report else "No target selected", size=16, color=COLORS["text"], weight=ft.FontWeight.BOLD), ft.Container(expand=True), ft.Button("Run scan", icon=ft.Icons.RADAR, on_click=lambda event: open_page("scan_center"))], wrap=True),
                section_picker,
                details,
            ],
            spacing=14,
            expand=True,
        ),
    )


def _simple_real_list(title, rows):
    if not rows:
        return empty_state(ft.Icons.INBOX_OUTLINED, "No data available", f"No {title.lower()} were returned by the latest scan.")
    return panel([ft.Text(row, size=12, color=COLORS["text"], selectable=True) for row in rows], title=title)


def _tool_page(page, page_id):
    labels = {
        "dns_lookup": ("DNS Lookup", "DNS resolver exists in Phase 1; this standalone tool view is not wired yet."),
        "port_scanner": ("Port Scanner", "Use Scan Center for the connected Phase 1 TCP inventory."),
        "http_inspector": ("HTTP Inspector", "HTTP inspection is not in the connected scanner output."),
        "tls_inspector": ("TLS Inspector", "TLS inspection is not connected yet."),
        "header_analyzer": ("Header Analyzer", "Header analysis is not connected yet."),
        "cookie_analyzer": ("Cookie Analyzer", "Cookie analysis is not connected yet."),
        "technology_detector": ("Technology Detector", "Technology fingerprinting is not connected yet."),
        "url_analyzer": ("URL Analyzer", "Target URL profiling is available in Scan Center."),
    }
    title, description = labels[page_id]
    target = ft.TextField(label="Target URL or hostname", hint_text="Authorized target only", expand=True)
    options = ft.Row(
        [
            ft.Dropdown(label="Profile", width=180, value="Default", options=[ft.dropdown.Option(item) for item in ["Default", "Conservative", "Extended"]]),
            ft.Switch(label="Include additional checks", value=False),
        ],
        wrap=True,
    )
    result = ft.Container(content=empty_state(ft.Icons.INBOX_OUTLINED, "No results", description), expand=True)

    def run_tool(event):
        result.content = empty_state(ft.Icons.INFO_OUTLINED, "Backend not connected", description)
        event.page.update()

    return ft.Container(
        expand=True,
        padding=24,
        content=ft.Column(
            [
                page_heading("Tools", title, description),
                panel([target, options, ft.Button("Run", icon=ft.Icons.PLAY_ARROW, on_click=run_tool)], title="Configuration"),
                panel([result], title="Result", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )


def _settings_page(page):
    groups = {
        "GENERAL": ["Notifications", "Auto save", "Confirm before delete"],
        "SCANNER": ["DNS", "Subdomain", "Host", "Port"],
        "OUTPUT": ["JSON", "TXT", "HTML", "PDF"],
        "APPEARANCE": ["Compact layout", "Animations"],
        "MODULES": ["DNS", "Subdomain", "Host", "Port", "Web", "TLS", "Headers", "Technology", "Reports"],
    }
    status = ft.Text("Settings apply to this UI session only.", size=10, color=COLORS["muted"])
    cards = []
    for title, labels in groups.items():
        rows = []
        for label in labels:
            control = ft.Switch(value=label in {"Notifications", "Auto save", "DNS", "Subdomain", "Host", "Port", "JSON", "TXT", "PDF", "Reports", "Animations"}, active_color=COLORS["accent"])
            control.on_change = lambda event, selected=label: setattr(status, "value", f"{selected} preference changed for this session.")
            rows.append(ft.Row([ft.Text(label, size=11, color=COLORS["text"], expand=True), control]))
        cards.append(ft.Container(content=panel(rows, title=title), col={"xs": 12, "lg": 6}))
    defaults = panel(
        [
            ft.Dropdown(label="Startup page", value="Dashboard", options=[ft.dropdown.Option(item) for item in ["Dashboard", "Scan Center", "Targets"]]),
            ft.Dropdown(label="Default format", value="PDF", options=[ft.dropdown.Option(item) for item in ["JSON", "TXT", "HTML", "PDF"]]),
            ft.TextField(label="Report location", hint_text="Choose when exporting", read_only=True),
            status,
        ],
        title="Defaults",
    )
    return ft.Container(expand=True, padding=24, content=ft.Column([page_heading("System", "Settings", "Session-only interface preferences; backend configuration is not changed."), ft.ResponsiveRow([ft.Container(content=defaults, col={"xs": 12, "lg": 6}), *cards], spacing=12, run_spacing=12)], spacing=14, scroll=ft.ScrollMode.AUTO))


def _custom_scan(page):
    sections = {
        "DISCOVERY": ["DNS", "Subdomains", "IP / Hosts", "Ports", "Services"],
        "WEB DISCOVERY": ["Crawling", "URLs", "Endpoints", "Parameters", "APIs", "JavaScript"],
        "WEB INTELLIGENCE": ["Technologies", "TLS", "Security Headers", "Cookies", "Authentication Surface"],
        "ANALYSIS": ["Findings", "Evidence", "Risk Analysis"],
        "OUTPUT": ["JSON", "TXT", "HTML", "PDF"],
    }
    cards = []
    for title, labels in sections.items():
        rows = [ft.Checkbox(label=label, value=label in {"DNS", "Subdomains", "IP / Hosts", "Ports", "Services", "JSON"}, active_color=COLORS["accent"]) for label in labels]
        cards.append(ft.Container(content=panel(rows, title=title), col={"xs": 12, "md": 6, "xl": 4}))
    status = ft.Text("Configuration is UI-only. Run Phase 1 from Scan Center.", size=11, color=COLORS["muted"])
    settings = panel(
        [
            ft.ResponsiveRow([
                ft.Container(content=ft.TextField(label="Timeout (seconds)", value="30"), col={"xs": 12, "sm": 6, "lg": 3}),
                ft.Container(content=ft.Dropdown(label="Scan speed", value="Conservative", options=[ft.dropdown.Option(item) for item in ["Slow", "Conservative", "Balanced"]]), col={"xs": 12, "sm": 6, "lg": 3}),
                ft.Container(content=ft.Dropdown(label="Port range", value="Common ports", options=[ft.dropdown.Option(item) for item in ["Common ports", "Custom list", "Full TCP range"]]), col={"xs": 12, "sm": 6, "lg": 3}),
                ft.Container(content=ft.TextField(label="Request limit", value="500"), col={"xs": 12, "sm": 6, "lg": 3}),
                ft.Container(content=ft.TextField(label="Wordlist path", hint_text="Optional local wordlist"), col={"xs": 12, "lg": 6}),
            ], spacing=10, run_spacing=10),
            ft.Button("Save configuration", icon=ft.Icons.SAVE_OUTLINED, on_click=lambda event: setattr(status, "value", "Configuration saved for this session only.")),
            status,
        ],
        title="Scan configuration",
    )
    return ft.Container(expand=True, padding=24, content=ft.Column([page_heading("Scan", "Custom scan", "Select modules and scan limits. Controls are not connected to backend settings yet."), ft.ResponsiveRow(cards, spacing=10, run_spacing=10), settings], spacing=14, scroll=ft.ScrollMode.AUTO))


def _scan_center(page, open_page):
    latest = get_latest_report()
    target_label = latest["target"]["hostname"] if latest else "No active target"
    stage_names = ["Target profile", "DNS intelligence", "Subdomain discovery", "Host discovery", "Port discovery", "Web discovery", "Analysis"]
    stage_rows = [ft.Row([ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=15, color=COLORS["muted"]), ft.Text(stage, size=11, color=COLORS["muted"]), ft.Container(expand=True), status_badge("Not run", COLORS["muted"])]) for stage in stage_names]
    return ft.Container(
        expand=True,
        padding=24,
        content=ft.Column(
            [
                page_heading("Scan", "Scan center", "Launch the connected Phase 1 scanner or review scan profiles."),
                panel([
                    ft.Text("Current target", size=10, color=COLORS["muted"]),
                    ft.Text(target_label, size=17, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Dropdown(label="Scan profile", value="Standard", options=[ft.dropdown.Option(item) for item in ["Quick Scan", "Standard Scan", "Deep Scan", "Custom Scan"]]),
                    ft.Text("Phase 1 uses DNS/subdomain/host/port modules. Web and analysis stages remain unavailable until connected.", size=11, color=COLORS["muted"]),
                    ft.Row([
                        ft.Button("Start Phase 1 Scan", icon=ft.Icons.PLAY_ARROW, on_click=lambda event: open_page("quick_scan")),
                        ft.OutlinedButton("Stop", icon=ft.Icons.STOP, on_click=lambda event: show_notice(event.page, "No scan is running.")),
                        ft.OutlinedButton("Pause", icon=ft.Icons.PAUSE, on_click=lambda event: show_notice(event.page, "No scan is running.")),
                        ft.TextButton("Clear", on_click=lambda event: open_page("scan_center")),
                    ], wrap=True),
                ], title="Scan configuration"),
                panel(stage_rows, title="Scan stages", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )


def _live_scan(page):
    report = get_latest_report()
    if report:
        details = [
            f"Last completed target: {report['target']['hostname']}",
            f"DNS status: {report['dns']['status']}",
            f"Resolved hosts: {len(report.get('hosts', []))}",
            f"Open ports: {len(report.get('ports', []))}",
        ]
        state = panel([ft.Text(line, size=12, color=COLORS["text"]) for line in details], title="Latest real scan")
    else:
        state = empty_state(ft.Icons.TRACK_CHANGES, "No live scan", "Start a Phase 1 scan to populate real scanner results here.")
    stages = panel([empty_state(ft.Icons.INFO_OUTLINE, "Live progress unavailable", "The current scanner returns results on completion and does not emit live stage updates.")], title="Progress")
    return ft.Container(expand=True, padding=24, content=ft.Column([page_heading("Scan", "Live scan", "Live metrics appear only when the scanner provides them."), state, stages], spacing=14, scroll=ft.ScrollMode.AUTO))


def build_workspace_page(page, page_id, open_page):
    if page_id in TABLE_SPECS:
        return _table_page(page, page_id, open_page)
    if page_id == "asset_graph":
        return _asset_graph(page)
    if page_id == "target_explorer":
        return _target_explorer(page, open_page)
    if page_id == "settings":
        return _settings_page(page)
    if page_id == "custom_scan":
        return _custom_scan(page)
    if page_id == "scan_center":
        return _scan_center(page, open_page)
    if page_id == "live_scan":
        return _live_scan(page)
    return _tool_page(page, page_id)


def real_records_for_search():
    records = []
    for page_id in ("targets", "assets", "network", "scan_history", "reports"):
        for record in _records(page_id):
            records.extend(str(value) for value in record.values() if value)
    report = get_latest_report()
    if report:
        records.extend(item.get("hostname", "") for item in report.get("subdomain_discovery", {}).get("results", []))
    return records


def real_notifications():
    return [
        (
            f"Scan completed · {report['target']['hostname']}",
            f"{len(report.get('hosts', []))} hosts · {len(report.get('ports', []))} open ports",
            report.get("_session", {}).get("started_at", ""),
        )
        for report in reversed(get_report_history())
    ]