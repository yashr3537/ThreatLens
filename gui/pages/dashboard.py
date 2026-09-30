import flet as ft

from ..components import COLORS, empty_state, metric, page_heading, panel, severity_badge, status_badge
from ..workspace_data import (
    get_all_findings,
    get_all_history,
    get_all_targets,
    get_all_network,
)
from .scan_url import SCANNER_PATH, get_latest_report


def create_dashboard(open_page):
    targets = get_all_targets()
    findings = get_all_findings()
    history = get_all_history()
    network = get_all_network()

    total_assets = sum(t.get("assets") or 0 for t in targets)
    critical_count = sum(1 for f in findings if f["severity"] == "Critical")
    high_count = sum(1 for f in findings if f["severity"] == "High")
    medium_count = sum(1 for f in findings if f["severity"] == "Medium")
    low_count = sum(1 for f in findings if f["severity"] in ("Low", "Info"))

    top_metrics = [
        metric("Total Targets", len(targets), "Active in workspace", ft.Icons.PUBLIC, COLORS["accent"]),
        metric("Total Assets", total_assets, "Discovered hosts & IPs", ft.Icons.INVENTORY_2_OUTLINED, COLORS["blue"]),
        metric("Total Scans", len(history), "Recon sessions completed", ft.Icons.RADAR, COLORS["lime"]),
        metric("Total Findings", len(findings) if findings else "N/A", "Analysis unavailable" if not findings else "Detected vulnerabilities", ft.Icons.BUG_REPORT_OUTLINED, COLORS["muted"] if not findings else COLORS["red"]),
    ]

    severity_metrics = [
        metric("Critical Findings", critical_count if findings else "N/A", "Analysis unavailable" if not findings else "Immediate remediation", ft.Icons.ERROR_OUTLINE, COLORS["red"] if findings else COLORS["muted"]),
        metric("High Findings", high_count if findings else "N/A", "Analysis unavailable" if not findings else "Exploitable surface", ft.Icons.WARNING_AMBER, COLORS["amber"] if findings else COLORS["muted"]),
        metric("Medium Findings", medium_count if findings else "N/A", "Analysis unavailable" if not findings else "Misconfigurations", ft.Icons.INFO_OUTLINED, COLORS["blue"] if findings else COLORS["muted"]),
        metric("Low & Info", low_count if findings else "N/A", "Analysis unavailable" if not findings else "Hardening items", ft.Icons.SHIELD_OUTLINED, COLORS["muted"]),
    ]

    metric_grid = ft.ResponsiveRow(
        [ft.Container(content=card, col={"xs": 6, "md": 3}) for card in top_metrics],
        spacing=10,
        run_spacing=10,
    )
    severity_grid = ft.ResponsiveRow(
        [ft.Container(content=card, col={"xs": 6, "md": 3}) for card in severity_metrics],
        spacing=10,
        run_spacing=10,
    )

    # Recent Scans Table
    scan_rows = []
    for h in history[:6]:
        findings_badge = status_badge(
            f"{h['findings']} Findings" if h.get("findings") is not None else "N/A",
            COLORS["amber"] if h.get("findings") else COLORS["muted"],
        )
        scan_rows.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.LANGUAGE, size=15, color=COLORS["accent"]),
                        ft.Text(h["target"], size=12, color=COLORS["text"], weight=ft.FontWeight.W_500, expand=2),
                        ft.Text(h["scan_type"], size=11, color=COLORS["muted"], expand=1),
                        status_badge(h["status"], COLORS["lime"] if h["status"] == "Completed" else COLORS["amber"]),
                        ft.Container(content=findings_badge, width=100),
                        ft.Text(h["duration"], size=11, color=COLORS["muted"], width=70),
                        ft.Text(h["start_time"], size=10, color=COLORS["muted"], width=130),
                        ft.TextButton("View", on_click=lambda e: open_page("reports")),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                bgcolor=COLORS["raised"],
                border_radius=6,
            )
        )

    recent_scans_panel = panel(
        scan_rows,
        title="Recent Recon Scans",
        trailing=ft.TextButton("View All Scans", on_click=lambda e: open_page("scan_history")),
    )

    # System Status
    scanner_ready = SCANNER_PATH.is_file()
    system_modules = [
        ("Scanner Engine (C++17)", "READY" if scanner_ready else "COMPILING", COLORS["lime"] if scanner_ready else COLORS["amber"]),
        ("Network Module (TCP/UDP)", "READY", COLORS["lime"]),
        ("DNS Intelligence Module", "READY", COLORS["lime"]),
        ("Web Engine (Crawler & HTTP)", "NOT CONNECTED", COLORS["muted"]),
        ("Report Engine (PDF/HTML/JSON)", "READY", COLORS["lime"]),
    ]

    status_items = [
        ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(width=6, height=6, bgcolor=tone, border_radius=3),
                        ft.Text(name, size=11, color=COLORS["text"]),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                status_badge(status, tone),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        for name, status, tone in system_modules
    ]
    system_status_panel = panel(status_items, title="System & Engine Status")

    # Activity / Recent Events Feed
    activity_rows = [
        ft.Row(
            [
                ft.Icon(icon, size=16, color=color),
                ft.Column(
                    [
                        ft.Text(title, size=11, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                        ft.Text(desc, size=10, color=COLORS["muted"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Text(time_str, size=9, color=COLORS["muted"]),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        for icon, color, title, desc, time_str in [
            (ft.Icons.CHECK_CIRCLE, COLORS["lime"], "Phase 1 scan completed", f"{item['target']} · {item['start_time']}", item["start_time"])
            for item in history[:8]
        ]
    ]
    activity_panel = panel(activity_rows or [empty_state(ft.Icons.NOTIFICATIONS_NONE, "No activity", "Activity appears after a real scan completes.")], title="Security Activity Feed")

    # Quick Actions Bar
    quick_actions = ft.Row(
        [
            ft.Button("Launch Scan", icon=ft.Icons.RADAR, on_click=lambda e: open_page("scan_center")),
            ft.Button("Quick Phase 1 Scan", icon=ft.Icons.FLASH_ON, on_click=lambda e: open_page("quick_scan")),
            ft.OutlinedButton("Vulnerabilities", icon=ft.Icons.BUG_REPORT, on_click=lambda e: open_page("findings")),
            ft.OutlinedButton("Asset Graph", icon=ft.Icons.HUB, on_click=lambda e: open_page("asset_graph")),
            ft.OutlinedButton("Security Tools", icon=ft.Icons.CONSTRUCTION, on_click=lambda e: open_page("dns_lookup")),
        ],
        spacing=10,
        wrap=True,
    )

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading("Workspace", "Security Operations Dashboard", "Real-time attack surface posture, recon status, and vulnerability overview.", quick_actions),
                metric_grid,
                severity_grid,
                ft.ResponsiveRow(
                    [
                        ft.Container(content=recent_scans_panel, col={"xs": 12, "lg": 8}),
                        ft.Container(content=system_status_panel, col={"xs": 12, "lg": 4}),
                    ],
                    spacing=12,
                    run_spacing=12,
                ),
                activity_panel,
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )