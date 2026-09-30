import flet as ft
from urllib.parse import urlsplit

from ..components import COLORS, empty_state, page_heading, panel, show_toast, status_badge
from ..workspace_data import get_all_endpoints


def create_endpoints_page(page, open_page):
    search_input = ft.TextField(
        hint_text="Filter endpoints by URL or parameter...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=280,
        dense=True,
    )
    method_filter = ft.Dropdown(
        label="HTTP Method",
        value="All",
        width=140,
        dense=True,
        options=[ft.dropdown.Option(m) for m in ["All", "GET", "POST", "PUT", "DELETE"]],
    )
    type_filter = ft.Dropdown(
        label="Endpoint Type",
        value="All",
        width=140,
        dense=True,
        options=[ft.dropdown.Option(t) for t in ["All", "API", "Static", "Dynamic"]],
    )

    table_container = ft.Container(expand=True)
    count_text = ft.Text(size=11, color=COLORS["muted"])

    def method_badge(m):
        colors_map = {
            "GET": COLORS["lime"],
            "POST": COLORS["blue"],
            "PUT": COLORS["amber"],
            "DELETE": COLORS["red"],
            "PATCH": COLORS["purple"],
        }
        return status_badge(m, colors_map.get(m, COLORS["muted"]))

    def inspect_endpoint(ep):
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        method_badge(ep["method"]),
                        ft.Text(ep["url"], size=13, weight=ft.FontWeight.BOLD, color=COLORS["text"], expand=True),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row([ft.Text("Status Code:", size=11, color=COLORS["muted"], width=110), status_badge(f"HTTP {ep['status']}", COLORS["lime"] if ep['status'] == '200' else COLORS["amber"])]),
                            ft.Row([ft.Text("Type:", size=11, color=COLORS["muted"], width=110), status_badge(ep["type"], COLORS["purple"])]),
                            ft.Row([ft.Text("Discovery Source:", size=11, color=COLORS["muted"], width=110), ft.Text(ep["source"], size=11, color=COLORS["cyan"])]),
                            ft.Row([ft.Text("Parameters:", size=11, color=COLORS["muted"], width=110), ft.Text(ep["params"], size=11, font_family="Consolas, Courier", color=COLORS["text"])]),
                            ft.Divider(color=COLORS["line"]),
                            ft.Text("REQUEST PREVIEW", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Text(f"{ep['method']} {ep['url']} HTTP/1.1\nHost: {urlsplit(ep['url']).hostname or ''}\nAccept: */*\n", size=10, font_family="Consolas, Courier", color=COLORS["text"]),
                                bgcolor="#05080E",
                                padding=8,
                                border_radius=6,
                                border=ft.Border.all(1, COLORS["line"]),
                            ),
                        ],
                        spacing=6,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    width=540,
                    height=280,
                ),
                actions=[
                    ft.Button("Close", on_click=lambda e: page.pop_dialog()),
                ],
            )
        )

    def render_table(e=None):
        q = (search_input.value or "").strip().lower()
        m = method_filter.value
        t = type_filter.value

        all_eps = get_all_endpoints(method=m, endpoint_type=t, search=q)
        count_text.value = f"{len(all_eps)} endpoints indexed"

        if not all_eps:
            table_container.content = empty_state(
                ft.Icons.ROUTE,
                "No endpoints match criteria",
                "Try clearing or adjusting your search term or method filter.",
            )
        else:
            rows = []
            for ep in all_eps:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(method_badge(ep["method"])),
                            ft.DataCell(ft.Text(ep["url"], size=12, color=COLORS["text"], weight=ft.FontWeight.W_500, selectable=True)),
                            ft.DataCell(status_badge(f"HTTP {ep['status']}", COLORS["lime"] if ep["status"] == "200" else (COLORS["amber"] if ep["status"].startswith("4") else COLORS["blue"]))),
                            ft.DataCell(status_badge(ep["type"], COLORS["purple"] if ep["type"] == "API" else COLORS["cyan"])),
                            ft.DataCell(ft.Text(ep["params"], size=11, font_family="Consolas, Courier", color=COLORS["muted"])),
                            ft.DataCell(ft.Text(ep["source"], size=11, color=COLORS["muted"])),
                            ft.DataCell(ft.Button("Inspect", icon=ft.Icons.INFO_OUTLINE, on_click=lambda ev, epo=ep: inspect_endpoint(epo))),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("METHOD", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("URL / ROUTE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("STATUS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("TYPE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("PARAMETERS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("SOURCE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ACTION", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
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
    method_filter.on_change = render_table
    type_filter.on_change = render_table
    render_table()

    toolbar = ft.Row(
        [
            search_input,
            method_filter,
            type_filter,
            ft.Container(expand=True),
            count_text,
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh Endpoints", on_click=render_table),
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
                    "Endpoint Explorer",
                    "Discovered API routes, web pages, and static assets extracted via crawling and JavaScript bundle analysis.",
                ),
                panel([toolbar, table_container], title="Discovered URL & API Surface", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )
