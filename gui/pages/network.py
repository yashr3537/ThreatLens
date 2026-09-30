import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, show_toast, status_badge
from ..workspace_data import get_all_network


def create_network_page(page, open_page):
    search_input = ft.TextField(
        hint_text="Search by IP, port, service, banner...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=260,
        dense=True,
    )
    protocol_filter = ft.Dropdown(
        label="Protocol",
        value="All",
        width=130,
        dense=True,
        options=[ft.dropdown.Option(p) for p in ["All", "TCP", "UDP"]],
    )
    state_filter = ft.Dropdown(
        label="Port State",
        value="All",
        width=140,
        dense=True,
        options=[ft.dropdown.Option(s) for s in ["All", "Open", "Filtered", "Closed"]],
    )

    table_container = ft.Container(expand=True)
    count_text = ft.Text(size=11, color=COLORS["muted"])

    def inspect_port(item):
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.Icon(ft.Icons.ROUTER, color=COLORS["accent"], size=20),
                        ft.Text(f"Port {item['port']}/{item['protocol']} Details", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row([ft.Text("Host:", size=11, color=COLORS["muted"], width=100), ft.Text(item["host"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD)]),
                            ft.Row([ft.Text("IP Address:", size=11, color=COLORS["muted"], width=100), ft.Text(item["address"], size=12, color=COLORS["text"])]),
                            ft.Row([ft.Text("Port / Protocol:", size=11, color=COLORS["muted"], width=100), ft.Text(f"{item['port']} / {item['protocol']}", size=12, color=COLORS["accent"], weight=ft.FontWeight.BOLD)]),
                            ft.Row([ft.Text("Service:", size=11, color=COLORS["muted"], width=100), status_badge(item["service"], COLORS["blue"])]),
                            ft.Row([ft.Text("State:", size=11, color=COLORS["muted"], width=100), status_badge(item["state"], COLORS["lime"] if item["state"] == "Open" else COLORS["amber"])]),
                            ft.Divider(color=COLORS["line"]),
                            ft.Text("SERVICE BANNER / FINGERPRINT", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Text(item["version"], size=11, font_family="Consolas, Courier", color=COLORS["text"], selectable=True),
                                bgcolor="#05080E",
                                padding=8,
                                border_radius=6,
                                border=ft.Border.all(1, COLORS["line"]),
                            ),
                        ],
                        spacing=8,
                        tight=True,
                    ),
                    width=480,
                ),
                actions=[
                    ft.Button("Close", on_click=lambda e: page.pop_dialog()),
                ],
            )
        )

    def render_table(e=None):
        q = (search_input.value or "").strip().lower()
        proto = protocol_filter.value
        st = state_filter.value

        all_network = get_all_network(protocol=proto, state=st, search=q)
        count_text.value = f"{len(all_network)} network ports detected"

        if not all_network:
            table_container.content = empty_state(
                ft.Icons.LAN,
                "No open ports match criteria",
                "Try clearing or modifying the protocol or search filters.",
            )
        else:
            rows = []
            for item in all_network:
                state_tone = COLORS["lime"] if item["state"] == "Open" else (COLORS["amber"] if item["state"] == "Filtered" else COLORS["red"])
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(item["address"], size=11, font_family="Consolas, Courier", color=COLORS["text"], weight=ft.FontWeight.BOLD, selectable=True)),
                            ft.DataCell(ft.Text(item["host"], size=11, color=COLORS["muted"], selectable=True)),
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Text(f"{item['port']}/{item['protocol']}", size=11, weight=ft.FontWeight.BOLD, color=COLORS["accent"]),
                                    ],
                                    spacing=4,
                                )
                            ),
                            ft.DataCell(status_badge(item["service"], COLORS["blue"])),
                            ft.DataCell(status_badge(item["state"], state_tone)),
                            ft.DataCell(ft.Text(item["version"], size=10, color=COLORS["muted"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)),
                            ft.DataCell(ft.Button("Inspect", icon=ft.Icons.INFO_OUTLINE, on_click=lambda ev, net_item=item: inspect_port(net_item))),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("IP ADDRESS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("HOST / DOMAIN", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("PORT / PROTO", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("SERVICE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("STATE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("VERSION / BANNER", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
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
    protocol_filter.on_change = render_table
    state_filter.on_change = render_table
    render_table()

    toolbar = ft.Row(
        [
            search_input,
            protocol_filter,
            state_filter,
            ft.Container(expand=True),
            count_text,
            ft.Button("Run Port Scan", icon=ft.Icons.RADAR, on_click=lambda e: open_page("port_scanner")),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh Network", on_click=render_table),
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
                    "Network & Port Inventory",
                    "Active TCP/UDP listening services, banners, and network accessibility returned from multi-threaded scans.",
                ),
                panel([toolbar, table_container], title="Discovered Ports & Network Services", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )
