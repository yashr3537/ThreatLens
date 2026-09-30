import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, severity_badge, show_toast, status_badge, tag_chip
from ..workspace_data import (
    get_all_findings,
    get_all_targets,
    update_finding_notes,
    update_finding_status,
)


def create_findings_page(page, open_page):
    findings_list = get_all_findings()

    critical_count = sum(1 for f in findings_list if f["severity"] == "Critical")
    high_count = sum(1 for f in findings_list if f["severity"] == "High")
    medium_count = sum(1 for f in findings_list if f["severity"] == "Medium")
    low_count = sum(1 for f in findings_list if f["severity"] == "Low")
    info_count = sum(1 for f in findings_list if f["severity"] == "Info")

    summary_cards = [
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("CRITICAL", size=10, color=COLORS["red"], weight=ft.FontWeight.BOLD),
                    ft.Text(str(critical_count), size=24, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Text("RCE / Auth Bypass", size=9, color=COLORS["muted"]),
                ],
                spacing=2,
            ),
            padding=12,
            bgcolor=COLORS["panel"],
            border=ft.Border.all(1, COLORS["red"]),
            border_radius=8,
            expand=True,
        ),
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("HIGH", size=10, color=COLORS["orange"], weight=ft.FontWeight.BOLD),
                    ft.Text(str(high_count), size=24, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Text("Exploitable Surface", size=9, color=COLORS["muted"]),
                ],
                spacing=2,
            ),
            padding=12,
            bgcolor=COLORS["panel"],
            border=ft.Border.all(1, COLORS["orange"]),
            border_radius=8,
            expand=True,
        ),
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("MEDIUM", size=10, color=COLORS["amber"], weight=ft.FontWeight.BOLD),
                    ft.Text(str(medium_count), size=24, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Text("Misconfigurations", size=9, color=COLORS["muted"]),
                ],
                spacing=2,
            ),
            padding=12,
            bgcolor=COLORS["panel"],
            border=ft.Border.all(1, COLORS["amber"]),
            border_radius=8,
            expand=True,
        ),
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("LOW", size=10, color=COLORS["blue"], weight=ft.FontWeight.BOLD),
                    ft.Text(str(low_count), size=24, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Text("Version Disclosure", size=9, color=COLORS["muted"]),
                ],
                spacing=2,
            ),
            padding=12,
            bgcolor=COLORS["panel"],
            border=ft.Border.all(1, COLORS["blue"]),
            border_radius=8,
            expand=True,
        ),
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("INFO", size=10, color=COLORS["cyan"], weight=ft.FontWeight.BOLD),
                    ft.Text(str(info_count), size=24, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Text("Hygiene & Policy", size=9, color=COLORS["muted"]),
                ],
                spacing=2,
            ),
            padding=12,
            bgcolor=COLORS["panel"],
            border=ft.Border.all(1, COLORS["cyan"]),
            border_radius=8,
            expand=True,
        ),
    ]

    cards_row = ft.Row(summary_cards, spacing=10)

    # Filter controls
    search_input = ft.TextField(hint_text="Search findings by title, target, evidence...", prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]), width=250, dense=True)
    sev_filter = ft.Dropdown(
        label="Severity",
        value="All",
        width=130,
        dense=True,
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(s) for s in ["Critical", "High", "Medium", "Low", "Info"]],
    )
    cat_filter = ft.Dropdown(
        label="Category",
        value="All",
        width=140,
        dense=True,
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(c) for c in ["Injection", "Auth", "Headers", "Network", "TLS", "Cookies", "Web", "DNS"]],
    )
    target_names = ["All"] + [t["target"] for t in get_all_targets()]
    target_filter = ft.Dropdown(
        label="Target",
        value="All",
        width=180,
        dense=True,
        options=[ft.dropdown.Option(t) for t in target_names],
    )
    status_filter = ft.Dropdown(
        label="Status",
        value="All",
        width=130,
        dense=True,
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(st) for st in ["Open", "Review", "Reviewed", "Remediated"]],
    )

    table_container = ft.Container(expand=True)
    findings_count_text = ft.Text(size=11, color=COLORS["muted"])

    def open_finding_details(finding):
        notes_input = ft.TextField(value=finding.get("notes", ""), multiline=True, min_lines=2, hint_text="Add triage notes...")

        def mark_reviewed_click(ev):
            update_finding_status(finding["id"], "Reviewed")
            finding["status"] = "Reviewed"
            page.pop_dialog()
            render_findings()
            show_toast(page, f"Finding '{finding['title']}' marked as Reviewed.", COLORS["lime"])

        def save_note_click(ev):
            update_finding_notes(finding["id"], notes_input.value)
            finding["notes"] = notes_input.value
            page.pop_dialog()
            render_findings()
            show_toast(page, "Note saved to finding.", COLORS["lime"])

        def export_evidence_click(ev):
            clipboard = ft.Clipboard()
            page.services.append(clipboard)
            clipboard.set(f"Finding: {finding['title']}\nTarget: {finding['target']}\nEvidence:\n{finding['evidence']}")
            show_toast(page, "Evidence copied to clipboard.", COLORS["cyan"])

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        severity_badge(finding["severity"]),
                        ft.Text(finding["title"], size=14, weight=ft.FontWeight.BOLD, color=COLORS["text"], expand=True),
                        status_badge(finding["status"], COLORS["lime"] if finding["status"] == "Reviewed" else COLORS["amber"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row([ft.Text("Target:", size=11, color=COLORS["muted"], width=100), ft.Text(finding["target"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD)]),
                            ft.Row([ft.Text("Category:", size=11, color=COLORS["muted"], width=100), status_badge(finding["category"], COLORS["purple"])]),
                            ft.Row([ft.Text("Discovered:", size=11, color=COLORS["muted"], width=100), ft.Text(finding["date"], size=11, color=COLORS["muted"])]),
                            ft.Divider(color=COLORS["line"]),
                            ft.Text("DESCRIPTION", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Text(finding.get("description", "Vulnerability details."), size=11, color=COLORS["text"]),
                            ft.Container(height=4),
                            ft.Text("WHY IT MATTERS (IMPACT & RISK)", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Text(finding.get("why_it_matters", "Security impact."), size=11, color=COLORS["red"]),
                            ft.Container(height=4),
                            ft.Text("RAW EVIDENCE TRACE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Text(finding.get("evidence", "No evidence"), size=10, font_family="Consolas, Courier", color=COLORS["text"], selectable=True),
                                bgcolor="#05080E",
                                padding=8,
                                border_radius=6,
                                border=ft.Border.all(1, COLORS["line"]),
                            ),
                            ft.Container(height=4),
                            ft.Text("REMEDIATION RECOMMENDATION", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Text(finding.get("recommendation", "Remediation guidance."), size=11, color=COLORS["lime"]),
                            ft.Divider(color=COLORS["line"]),
                            notes_input,
                        ],
                        spacing=6,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    width=580,
                    height=440,
                ),
                actions=[
                    ft.TextButton("Export Evidence", icon=ft.Icons.COPY, on_click=export_evidence_click),
                    ft.TextButton("Save Note", on_click=save_note_click),
                    ft.Button("Mark Reviewed", icon=ft.Icons.CHECK, on_click=mark_reviewed_click),
                    ft.TextButton("Close", on_click=lambda ev: page.pop_dialog()),
                ],
            )
        )

    def render_findings(e=None):
        q = (search_input.value or "").strip()
        sev = sev_filter.value
        cat = cat_filter.value
        tgt = target_filter.value
        st = status_filter.value

        filtered = get_all_findings(
            severity=sev,
            category=cat,
            target=tgt,
            status=st,
            search=q,
        )

        findings_count_text.value = f"{len(filtered)} findings listed"

        if not filtered:
            table_container.content = empty_state(
                ft.Icons.SECURITY,
                "No findings match criteria",
                "Try adjusting your severity, category, or search filters.",
            )
        else:
            rows = []
            for f in filtered:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(severity_badge(f["severity"])),
                            ft.DataCell(
                                ft.Text(f["title"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD, selectable=True)
                            ),
                            ft.DataCell(ft.Text(f["target"], size=11, color=COLORS["muted"])),
                            ft.DataCell(status_badge(f["category"], COLORS["purple"])),
                            ft.DataCell(status_badge(f["status"], COLORS["lime"] if f["status"] == "Reviewed" else COLORS["amber"])),
                            ft.DataCell(
                                ft.Text(f["evidence"][:45] + ("..." if len(f["evidence"]) > 45 else ""), size=10, font_family="Consolas, Courier", color=COLORS["muted"])
                            ),
                            ft.DataCell(ft.Text(f["date"], size=10, color=COLORS["muted"])),
                            ft.DataCell(
                                ft.Button("Inspect", icon=ft.Icons.SEARCH, on_click=lambda ev, fnd=f: open_finding_details(fnd))
                            ),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("SEVERITY", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("TITLE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("TARGET", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("CATEGORY", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("STATUS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("EVIDENCE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("DATE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ACTION", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                column_spacing=16,
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

    search_input.on_change = render_findings
    sev_filter.on_change = render_findings
    cat_filter.on_change = render_findings
    target_filter.on_change = render_findings
    status_filter.on_change = render_findings
    render_findings()

    toolbar = ft.Row(
        [
            search_input,
            sev_filter,
            cat_filter,
            target_filter,
            status_filter,
            ft.Container(expand=True),
            findings_count_text,
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh Findings", on_click=render_findings),
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
                    "Analysis",
                    "Findings & Vulnerability Management",
                    "Prioritized security findings, CVE associations, configuration weaknesses, and mitigation steps.",
                ),
                cards_row,
                panel([toolbar, table_container], title="Detected Vulnerabilities & Exposures", expand=True),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
