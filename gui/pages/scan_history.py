import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, show_toast, status_badge
from ..workspace_data import get_all_history


def create_scan_history_page(page, open_page):
    search_input = ft.TextField(
        hint_text="Search historical scans by target or profile...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=280,
        dense=True,
    )
    status_filter = ft.Dropdown(
        label="Status",
        value="All",
        width=140,
        dense=True,
        options=[ft.dropdown.Option("All"), ft.dropdown.Option("Completed"), ft.dropdown.Option("Failed")],
    )

    history_data = get_all_history()
    table_container = ft.Container(expand=True)
    count_text = ft.Text(size=11, color=COLORS["muted"])

    def compare_scans_dialog(scan_a):
        scan_b_candidates = [s for s in history_data if s["id"] != scan_a["id"]]
        if not scan_b_candidates:
            show_toast(page, "A second real scan is required for comparison.", COLORS["amber"])
            return
        scan_b = scan_b_candidates[0]

        scan_b_dd = ft.Dropdown(
            label="Compare with Scan",
            value=scan_b["id"],
            options=[ft.dropdown.Option(s["id"], f"{s['target']} ({s['start_time'][:10]})") for s in scan_b_candidates],
        )

        report_a = scan_a.get("report") or {}
        report_b = scan_b.get("report") or {}
        ports_a = {
            (item.get("address"), item.get("port"), item.get("protocol"), item.get("service"))
            for item in report_a.get("ports", [])
        }
        ports_b = {
            (item.get("address"), item.get("port"), item.get("protocol"), item.get("service"))
            for item in report_b.get("ports", [])
        }
        subdomains_a = {item.get("hostname") for item in report_a.get("subdomain_discovery", {}).get("results", [])}
        subdomains_b = {item.get("hostname") for item in report_b.get("subdomain_discovery", {}).get("results", [])}
        diff_lines = [
            f"New open ports in A: {len(ports_a - ports_b)}",
            f"Open ports no longer present in A: {len(ports_b - ports_a)}",
            f"New resolved subdomains in A: {len(subdomains_a - subdomains_b)}",
            f"Subdomains no longer present in A: {len(subdomains_b - subdomains_a)}",
            "Finding difference: unavailable; Phase 1 does not analyze findings.",
        ]
        comparison_body = ft.Container(
            content=ft.Column(
                [
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("BASE SCAN (A)", size=10, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
                                        ft.Text(scan_a["target"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Date: {scan_a['start_time']}", size=10, color=COLORS["muted"]),
                                        ft.Text(f"Profile: {scan_a['scan_type']}", size=10, color=COLORS["muted"]),
                                        ft.Text(f"Findings: {scan_a['findings'] if scan_a.get('findings') is not None else 'N/A'}", size=11, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=3,
                                ),
                                col={"xs": 12, "sm": 6},
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("COMPARISON SCAN (B)", size=10, color=COLORS["cyan"], weight=ft.FontWeight.BOLD),
                                        ft.Text(scan_b["target"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Date: {scan_b['start_time']}", size=10, color=COLORS["muted"]),
                                        ft.Text(f"Profile: {scan_b['scan_type']}", size=10, color=COLORS["muted"]),
                                        ft.Text(f"Findings: {scan_b['findings'] if scan_b.get('findings') is not None else 'N/A'}", size=11, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=3,
                                ),
                                col={"xs": 12, "sm": 6},
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(color=COLORS["line"]),
                    ft.Text("DIFFERENCE ANALYSIS (DIFF)", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                    *[ft.Text(line, size=11, color=COLORS["muted"]) for line in diff_lines],
                ],
                spacing=8,
            ),
            width=540,
        )

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row([ft.Icon(ft.Icons.COMPARE_ARROWS, color=COLORS["accent"]), ft.Text("Recon Scan Diff & Comparison", size=15, weight=ft.FontWeight.BOLD)]),
                content=ft.Container(content=ft.Column([scan_b_dd, comparison_body], tight=True), width=560),
                actions=[
                    ft.Button("Close", on_click=lambda e: page.pop_dialog()),
                ],
            )
        )

    def delete_scan(item):
        if item in history_data:
            history_data.remove(item)
        render_table()
        show_toast(page, f"Scan history for {item['target']} removed.", COLORS["amber"])

    def render_table(e=None):
        q = (search_input.value or "").strip().lower()
        st = status_filter.value

        filtered = [
            h for h in history_data
            if (not q or q in h["target"].lower() or q in h["scan_type"].lower())
            and (st == "All" or h["status"].lower() == st.lower())
        ]
        count_text.value = f"{len(filtered)} scans recorded"

        if not filtered:
            table_container.content = empty_state(ft.Icons.HISTORY, "No scan history found", "Complete a scan or clear your filter criteria.")
        else:
            rows = []
            for h in filtered:
                finding_count = h.get("findings")
                finding_badge = status_badge(
                    f"{finding_count} Findings" if finding_count is not None else "N/A",
                    COLORS["amber"] if finding_count else COLORS["muted"],
                )
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.LANGUAGE, size=15, color=COLORS["accent"]),
                                        ft.Text(h["target"], size=12, color=COLORS["text"], weight=ft.FontWeight.W_500, selectable=True),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                            ),
                            ft.DataCell(ft.Text(h["scan_type"], size=11, color=COLORS["muted"])),
                            ft.DataCell(ft.Text(h["start_time"], size=10, color=COLORS["muted"])),
                            ft.DataCell(ft.Text(h["duration"], size=11, color=COLORS["muted"])),
                            ft.DataCell(status_badge(h["status"], COLORS["lime"] if h["status"] == "Completed" else COLORS["red"])),
                            ft.DataCell(finding_badge),
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Button("View", on_click=lambda ev: open_page("reports")),
                                        ft.OutlinedButton("Compare", icon=ft.Icons.COMPARE, on_click=lambda ev, scn=h: compare_scans_dialog(scn)),
                                        ft.IconButton(ft.Icons.REFRESH, tooltip="Rescan", on_click=lambda ev: open_page("scan_center")),
                                        ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Delete Record", on_click=lambda ev, scn=h: delete_scan(scn)),
                                    ],
                                    spacing=4,
                                )
                            ),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("TARGET", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("SCAN TYPE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("START TIME", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("DURATION", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("STATUS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("FINDINGS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ACTIONS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                column_spacing=18,
                horizontal_margin=12,
                heading_row_height=40,
                data_row_min_height=44,
                heading_row_color=COLORS["raised"],
                bgcolor=COLORS["panel"],
                border_radius=8,
            )
            table_container.content = ft.Row([data_table], scroll=ft.ScrollMode.AUTO)

        if e:
            page.update()

    search_input.on_change = render_table
    status_filter.on_change = render_table
    render_table()

    toolbar = ft.Row(
        [
            search_input,
            status_filter,
            ft.Container(expand=True),
            count_text,
            ft.Button("Start New Scan", icon=ft.Icons.RADAR, on_click=lambda e: open_page("scan_center")),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh History", on_click=render_table),
        ],
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading(
                    "Output",
                    "Scan History & Audits",
                    "Timeline of completed security scans, historical duration metrics, and comparative diff analysis.",
                ),
                panel([toolbar, table_container], title="Audit Logs & Historical Sessions", expand=True),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
