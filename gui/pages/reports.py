import json

import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, show_toast, status_badge
from ..workspace_data import get_all_reports
from .single_input import _report_html, _report_pdf, _report_text


def create_reports_page(page, open_page):
    reports = get_all_reports()
    search = ft.TextField(hint_text="Search real scan reports...", width=280, dense=True, prefix=ft.Icon(ft.Icons.SEARCH, size=16))
    format_filter = ft.Dropdown(label="Format", value="All", width=140, options=[ft.dropdown.Option(item) for item in ["All", "JSON", "TXT", "HTML", "PDF"]])
    count = ft.Text(size=10, color=COLORS["muted"])
    table_area = ft.Container(expand=True)

    async def export(report, extension):
        actual = report.get("report")
        if actual is None:
            show_toast(page, "This report has no scanner data to export.", COLORS["amber"])
            return
        if extension == "pdf":
            data = _report_pdf(actual)
        elif extension == "html":
            data = _report_html(actual).encode("utf-8")
        elif extension == "txt":
            data = _report_text(actual).encode("utf-8")
        else:
            data = json.dumps(actual, indent=2, ensure_ascii=False).encode("utf-8")

        picker = ft.FilePicker()
        page.services.append(picker)
        path = await picker.save_file(
            dialog_title="Export scanner report",
            file_name=f"{report['name']}.{extension}",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[extension],
            src_bytes=data,
        )
        show_toast(page, f"Report saved to {path}." if path else "Export cancelled.", COLORS["lime"] if path else COLORS["muted"])

    def view_report(report):
        actual = report.get("report")
        if actual is None:
            return
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(report["name"]),
                content=ft.Container(
                    content=ft.Text(_report_text(actual), size=11, font_family="Consolas", selectable=True),
                    width=640,
                    height=440,
                    padding=12,
                    bgcolor=COLORS["canvas"],
                ),
                actions=[ft.TextButton("Close", on_click=lambda event: page.pop_dialog())],
            )
        )

    def export_dialog(report):
        async def choose(event, extension):
            page.pop_dialog()
            await export(report, extension)

        def export_button(extension):
            async def on_export(event):
                await choose(event, extension)
            return ft.OutlinedButton(extension.upper(), on_click=on_export)

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Export real scan data"),
                content=ft.Row(
                    [export_button(extension) for extension in ("json", "txt", "html", "pdf")],
                    wrap=True,
                ),
                actions=[ft.TextButton("Cancel", on_click=lambda event: page.pop_dialog())],
            )
        )

    def render(event=None):
        query = (search.value or "").strip().lower()
        selected = format_filter.value or "All"
        filtered = [
            item for item in reports
            if (not query or query in f"{item['name']} {item['target']}".lower())
            and (selected == "All" or selected in item["format"])
        ]
        count.value = f"{len(filtered)} real reports"
        if not filtered:
            table_area.content = empty_state(ft.Icons.ARTICLE_OUTLINED, "No real reports yet", "Complete a Phase 1 scan to create an exportable report.")
        else:
            table = ft.DataTable(
                columns=[ft.DataColumn(ft.Text(label.upper(), size=9, color=COLORS["muted"])) for label in ["Report", "Target", "Scan date", "Findings", "Status", "Format", "Actions"]],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(item["name"], size=11, color=COLORS["text"], selectable=True)),
                        ft.DataCell(ft.Text(item["target"], size=11, color=COLORS["text"], selectable=True)),
                        ft.DataCell(ft.Text(item["scan_date"], size=10, color=COLORS["muted"])),
                        ft.DataCell(status_badge("N/A", COLORS["muted"])),
                        ft.DataCell(status_badge(item["status"], COLORS["lime"])),
                        ft.DataCell(status_badge(item["format"], COLORS["blue"])),
                        ft.DataCell(ft.Row([
                            ft.TextButton("View", on_click=lambda ev, report=item: view_report(report)),
                            ft.OutlinedButton("Export", on_click=lambda ev, report=item: export_dialog(report)),
                        ], spacing=4)),
                    ])
                    for item in filtered
                ],
                heading_row_color=COLORS["raised"],
                data_row_min_height=44,
                column_spacing=16,
                bgcolor=COLORS["panel"],
            )
            table_area.content = ft.Row([table], scroll=ft.ScrollMode.AUTO)
        if event:
            event.page.update()

    search.on_change = render
    format_filter.on_change = render
    render()

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading("Output", "Reports", "Only reports generated from real scanner results appear here.", ft.Button("Run scan", icon=ft.Icons.RADAR, on_click=lambda event: open_page("scan_center"))),
                panel([ft.Row([search, format_filter, ft.Container(expand=True), count], wrap=True), table_area], title="Real scanner reports", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )