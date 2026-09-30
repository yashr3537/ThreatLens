import flet as ft

from ..components import COLORS, empty_state, metric, page_heading, panel, status_badge
from .scan_url import get_latest_report


def create_live_scan_page(page, open_page):
    report = get_latest_report()
    if report is None:
        target_panel = empty_state(
            ft.Icons.TRACK_CHANGES,
            "No scan is running",
            "The current C++ scanner returns structured results when a scan completes; it does not stream live progress.",
        )
        progress = 0
        progress_label = "No active scan"
        metrics = [
            metric("Assets", "—", "No scan data", ft.Icons.INVENTORY_2_OUTLINED, COLORS["muted"]),
            metric("Subdomains", "—", "No scan data", ft.Icons.ACCOUNT_TREE, COLORS["muted"]),
            metric("Hosts", "—", "No scan data", ft.Icons.COMPUTER, COLORS["muted"]),
            metric("Open ports", "—", "No scan data", ft.Icons.LAN, COLORS["muted"]),
            metric("Endpoints", "N/A", "Module not connected", ft.Icons.ROUTE, COLORS["muted"]),
            metric("Findings", "N/A", "Module not connected", ft.Icons.BUG_REPORT_OUTLINED, COLORS["muted"]),
        ]
        stages = []
        log_lines = []
    else:
        target = report["target"]
        dns = report.get("dns", {})
        discovery = report.get("subdomain_discovery", {})
        hosts = report.get("hosts", [])
        ports = report.get("ports", [])
        profile = report.get("_session", {}).get("scan_profile", "common")
        captured = report.get("_session", {}).get("started_at", "")

        target_panel = panel(
            [
                ft.Text(target.get("input", ""), size=16, color=COLORS["text"], weight=ft.FontWeight.BOLD, selectable=True),
                ft.Text(f"{target.get('scheme', '')} · {target.get('hostname', '')} · {target.get('path', '/')}", size=11, color=COLORS["muted"]),
                ft.Text(f"Completed: {captured} · Port profile: {profile}", size=10, color=COLORS["muted"]),
            ],
            title="Latest completed target",
        )
        progress = 1
        progress_label = "Completed"
        metrics = [
            metric("Assets", sum(len(host.get("addresses", [])) for host in hosts), "Resolved IP addresses", ft.Icons.INVENTORY_2_OUTLINED, COLORS["blue"]),
            metric("Subdomains", len(discovery.get("results", [])), "DNS verified", ft.Icons.ACCOUNT_TREE, COLORS["accent"]),
            metric("Hosts", len(hosts), "Resolved host records", ft.Icons.COMPUTER, COLORS["lime"]),
            metric("Open ports", len(ports), "TCP inventory", ft.Icons.LAN, COLORS["amber"]),
            metric("Endpoints", "N/A", "Crawler not connected", ft.Icons.ROUTE, COLORS["muted"]),
            metric("Findings", "N/A", "Analysis not connected", ft.Icons.BUG_REPORT_OUTLINED, COLORS["muted"]),
        ]
        stage_values = [
            ("Target profile", "Completed"),
            ("DNS intelligence", dns.get("status", "Unavailable")),
            ("Subdomain discovery", f"{discovery.get('attempted', 0)} candidates"),
            ("Host discovery", f"{len(hosts)} host records"),
            ("Port discovery", f"{len(ports)} open ports"),
            ("Web discovery", "Not connected"),
            ("Analysis", "Not connected"),
        ]
        stages = [
            ft.Row(
                [ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE if value not in ("Not connected", "Unavailable") else ft.Icons.REMOVE_CIRCLE_OUTLINE, color=COLORS["lime"] if value not in ("Not connected", "Unavailable") else COLORS["muted"], size=16), ft.Text(name, size=11, color=COLORS["text"], expand=True), status_badge(value, COLORS["lime"] if value not in ("Not connected", "Unavailable") else COLORS["muted"])],
                spacing=8,
            )
            for name, value in stage_values
        ]
        log_lines = [
            f"Scan completed for {target.get('hostname', '')}",
            f"DNS status: {dns.get('status', 'unknown')} · {len(dns.get('addresses', []))} addresses",
            f"Subdomain candidates attempted: {discovery.get('attempted', 0)}",
            f"Resolved hosts: {len(hosts)} · Open TCP ports: {len(ports)}",
        ]
        log_lines.extend(f"{item.get('address')}:{item.get('port')} {item.get('service')}" for item in ports)

    stage_panel = panel(
        stages or [empty_state(ft.Icons.INFO_OUTLINED, "Progress unavailable", "There is no active scan to report.")],
        title="Phase 1 stages",
    )
    event_panel = panel(
        [ft.Text(line, size=11, color=COLORS["text"], selectable=True) for line in log_lines]
        or [empty_state(ft.Icons.NOTES_OUTLINED, "No scan events", "Complete a scan to see its real output summary.")],
        title="Scanner output summary",
    )

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading("Scan", "Scan status", "Only completed scanner results are shown; live progress is not emitted by the current backend."),
                target_panel,
                panel([ft.Row([ft.Text("Progress", size=11, color=COLORS["muted"]), ft.Text(progress_label, size=11, color=COLORS["text"])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.ProgressBar(value=progress, color=COLORS["accent"], bgcolor=COLORS["raised"])], title="Status"),
                ft.ResponsiveRow([ft.Container(content=item, col={"xs": 6, "md": 4, "lg": 2}) for item in metrics], spacing=8, run_spacing=8),
                ft.ResponsiveRow([ft.Container(content=stage_panel, col={"xs": 12, "lg": 5}), ft.Container(content=event_panel, col={"xs": 12, "lg": 7})], spacing=10, run_spacing=10),
                ft.Row([ft.OutlinedButton("Pause", disabled=True, icon=ft.Icons.PAUSE), ft.OutlinedButton("Stop", disabled=True, icon=ft.Icons.STOP), ft.TextButton("Scan Center", on_click=lambda event: open_page("scan_center"))], wrap=True),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )