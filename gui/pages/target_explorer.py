import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, status_badge
from ..workspace_data import get_all_endpoints, get_all_findings, get_all_network, get_all_targets, get_all_technologies


SECTIONS = ["Overview", "Domains", "Subdomains", "IP Addresses", "Ports", "Services", "URLs", "Endpoints", "APIs", "Technologies", "Findings"]


def create_target_explorer_page(page, open_page):
    targets = get_all_targets()
    target_dropdown = ft.Dropdown(
        label="Scanned target",
        value=targets[0]["target"] if targets else None,
        width=320,
        options=[ft.dropdown.Option(item["target"]) for item in targets],
        disabled=not targets,
    )
    selected_section = {"value": "Overview"}
    tabs = ft.Row(wrap=True, spacing=6)
    content = ft.Container(expand=True)

    def render_section(event=None):
        target_name = target_dropdown.value
        target_record = next((item for item in targets if item["target"] == target_name), None)
        report = target_record.get("report") if target_record else None
        section = selected_section["value"]
        if target_record is None:
            content.content = empty_state(ft.Icons.PUBLIC, "No scanned target", "Targets appear after a successful Phase 1 scan.")
        elif section == "Overview":
            summary = [
                f"Target: {target_record['target']}",
                f"Status: {target_record['status']}",
                f"Last scan: {target_record['last_scan'] or 'Unavailable'}",
                f"DNS status: {report.get('dns', {}).get('status', 'Unavailable') if report else 'Not scanned'}",
                f"Resolved addresses: {target_record.get('assets') if target_record.get('assets') is not None else 'Unavailable'}",
                f"Findings: {'Unavailable' if target_record.get('findings') is None else target_record['findings']}",
                f"Notes: {target_record.get('notes') or 'None'}",
                f"Tags: {', '.join(target_record.get('tags', [])) or 'None'}",
            ]
            content.content = panel([ft.Text(line, size=12, color=COLORS["text"], selectable=True) for line in summary], title="Real target profile")
        elif section in ("Domains", "Subdomains"):
            entries = []
            if report and section == "Domains":
                entries.append(f"{report['target']['hostname']} · root target · {report['dns']['status']}")
            if report and section == "Subdomains":
                entries.extend(f"{row['hostname']} · {row['status']} · {', '.join(row.get('addresses', []))}" for row in report.get("subdomain_discovery", {}).get("results", []))
            content.content = _list_or_empty(section, entries, "No matching domain data was returned by this scan.")
        elif section == "IP Addresses":
            entries = [f"{host['hostname']} · {address} · {host['status']}" for host in (report or {}).get("hosts", []) for address in host.get("addresses", [])]
            content.content = _list_or_empty(section, entries, "No IP addresses were returned by this scan.")
        elif section in ("Ports", "Services"):
            entries = [f"{item['address']} · {item['port']}/{item['protocol']} · {item['state']} · {item['service']} · {item['version'] or 'Version unavailable'}" for item in (report or {}).get("ports", [])]
            content.content = _list_or_empty(section, entries, "No open TCP port data was returned by this scan.")
        else:
            provider = {
                "URLs": "URL discovery is not connected.",
                "Endpoints": "Endpoint discovery is not connected.",
                "APIs": "API discovery is not connected.",
                "Technologies": "Technology detection is not connected.",
                "Findings": "Finding analysis is not connected.",
            }.get(section, "No data provider is connected.")
            records = {
                "Endpoints": get_all_endpoints(),
                "APIs": [item for item in get_all_endpoints() if item.get("type") == "API"],
                "Technologies": get_all_technologies(),
                "Findings": get_all_findings(),
            }.get(section, [])
            content.content = _list_or_empty(section, [str(item) for item in records], provider)
        if event:
            event.page.update()

    def select_section(section):
        selected_section["value"] = section
        for button in tabs.controls:
            active = button.data == section
            button.bgcolor = COLORS["accent"] if active else COLORS["raised"]
            button.content.color = COLORS["canvas"] if active else COLORS["text"]
        render_section()
        page.update()

    for section in SECTIONS:
        button = ft.Container(
            content=ft.Text(section, size=10, color=COLORS["canvas"] if section == "Overview" else COLORS["text"]),
            data=section,
            padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            bgcolor=COLORS["accent"] if section == "Overview" else COLORS["raised"],
            border=ft.Border.all(1, COLORS["line"]),
            border_radius=5,
            on_click=lambda event, value=section: select_section(value),
        )
        tabs.controls.append(button)

    target_dropdown.on_change = render_section
    render_section()
    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading("Targets", "Target explorer", "Inspect the latest real scan for a selected target."),
                ft.Row([target_dropdown, ft.Container(expand=True), ft.Button("Scan target", icon=ft.Icons.RADAR, on_click=lambda event: open_page("scan_center")), ft.IconButton(ft.Icons.HUB, tooltip="Open asset graph", on_click=lambda event: open_page("asset_graph"))], wrap=True),
                panel([tabs], title="Target sections", padding=10),
                content,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )


def _list_or_empty(title, entries, empty_message):
    if not entries:
        return empty_state(ft.Icons.INBOX_OUTLINED, f"No {title.lower()} data", empty_message)
    return panel([ft.Text(entry, size=11, color=COLORS["text"], selectable=True) for entry in entries], title=title)