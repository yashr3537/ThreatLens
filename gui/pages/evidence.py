import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, show_toast, status_badge
from ..workspace_data import get_all_evidence


def create_evidence_page(page, open_page):
    search_input = ft.TextField(
        hint_text="Search evidence by name, target...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=250,
        dense=True,
    )
    type_filter = ft.Dropdown(
        label="Evidence Type",
        value="All",
        width=160,
        dense=True,
        options=[ft.dropdown.Option(t) for t in ["All", "Screenshot", "HTTP Response", "Headers", "DNS Result", "Port Result", "Endpoint", "Technology"]],
    )

    all_evidence = get_all_evidence()
    selected_evidence = {"val": all_evidence[0] if all_evidence else None}

    preview_title = ft.Text(all_evidence[0]["name"] if all_evidence else "No Evidence Selected", size=13, weight=ft.FontWeight.BOLD, color=COLORS["text"])
    preview_type = status_badge(all_evidence[0]["type"] if all_evidence else "NONE", COLORS["accent"])
    preview_meta = ft.Text(f"{all_evidence[0]['target']} · {all_evidence[0]['captured']}" if all_evidence else "", size=11, color=COLORS["muted"])
    preview_content = ft.Text(
        all_evidence[0]["content"] if all_evidence else "",
        size=11,
        font_family="Consolas, Courier",
        color=COLORS["text"],
        selectable=True,
    )

    def select_evidence(ev):
        selected_evidence["val"] = ev
        preview_title.value = ev["name"]
        preview_type.content.value = ev["type"].upper()
        preview_meta.value = f"Target: {ev['target']} · Captured: {ev['captured']} · Size: {ev['size']}"
        preview_content.value = ev["content"]
        page.update()

    def copy_evidence(e):
        ev = selected_evidence["val"]
        if ev:
            clipboard = ft.Clipboard()
            page.services.append(clipboard)
            clipboard.set(ev["content"])
            show_toast(page, "Evidence content copied to clipboard.", COLORS["cyan"])

    preview_panel = panel(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.FINGERPRINT, size=18, color=COLORS["accent"]),
                    ft.Column([preview_title, preview_meta], spacing=1, expand=True),
                    preview_type,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Divider(color=COLORS["line"]),
            ft.Container(
                content=ft.Column([preview_content], scroll=ft.ScrollMode.AUTO),
                bgcolor="#05080E",
                padding=12,
                border_radius=6,
                border=ft.Border.all(1, COLORS["line"]),
                height=300,
            ),
            ft.Row(
                [
                    ft.Button("Copy to Clipboard", icon=ft.Icons.COPY, on_click=copy_evidence),
                    ft.OutlinedButton("Export Raw Artifact", icon=ft.Icons.DOWNLOAD, on_click=lambda e: show_toast(page, "Evidence downloaded.")),
                ],
                spacing=8,
            ),
        ],
        title="Evidence Artifact Inspector",
    )

    table_container = ft.Container(expand=True)
    count_text = ft.Text(size=11, color=COLORS["muted"])

    def render_table(e=None):
        q = (search_input.value or "").strip().lower()
        t = type_filter.value

        filtered = [
            item for item in all_evidence
            if (not q or q in item["name"].lower() or q in item["target"].lower() or q in item["content"].lower())
            and (t == "All" or item["type"].lower() == t.lower())
        ]
        count_text.value = f"{len(filtered)} evidence items"

        if not filtered:
            table_container.content = empty_state(ft.Icons.FOLDER_OFF, "No evidence artifacts found", "Try clearing your search query or filter.")
        else:
            rows = []
            for item in filtered:
                is_sel = selected_evidence["val"] and selected_evidence["val"]["id"] == item["id"]
                type_tone = {
                    "HTTP Response": COLORS["blue"],
                    "Headers": COLORS["orange"],
                    "DNS Result": COLORS["cyan"],
                    "Port Result": COLORS["amber"],
                    "Technology": COLORS["purple"],
                    "Screenshot": COLORS["lime"],
                    "Endpoint": COLORS["accent"],
                }.get(item["type"], COLORS["muted"])

                rows.append(
                    ft.DataRow(
                        selected=is_sel,
                        on_select_change=lambda e, itm=item: select_evidence(itm),
                        cells=[
                            ft.DataCell(status_badge(item["type"], type_tone)),
                            ft.DataCell(ft.Text(item["name"], size=12, color=COLORS["text"], weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(item["target"], size=11, color=COLORS["muted"])),
                            ft.DataCell(ft.Text(item["captured"], size=10, color=COLORS["muted"])),
                            ft.DataCell(ft.Text(item["size"], size=10, font_family="Consolas, Courier", color=COLORS["muted"])),
                            ft.DataCell(ft.Button("Inspect", icon=ft.Icons.PREVIEW, on_click=lambda ev, itm=item: select_evidence(itm))),
                        ],
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("TYPE", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ARTIFACT NAME", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("TARGET", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("CAPTURED", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("SIZE", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ACTION", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                column_spacing=16,
                heading_row_height=38,
                data_row_min_height=42,
                heading_row_color=COLORS["raised"],
                bgcolor=COLORS["panel"],
                border_radius=8,
            )
            table_container.content = ft.Row([data_table], scroll=ft.ScrollMode.AUTO)

        if e:
            page.update()

    search_input.on_change = render_table
    type_filter.on_change = render_table
    render_table()

    toolbar = ft.Row(
        [
            search_input,
            type_filter,
            ft.Container(expand=True),
            count_text,
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh Evidence", on_click=render_table),
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
                    "Evidence Locker & Artifacts",
                    "Cryptographically timestamped forensic evidence including raw HTTP responses, banners, DNS traces, and headers.",
                ),
                panel([toolbar, table_container], title="Captured Security Artifacts"),
                preview_panel,
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
