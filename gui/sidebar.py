import flet as ft

from components import COLORS
from nav_items import NAV_SECTIONS


def create_sidebar(on_navigate, active_page="dashboard"):
    item_controls = {}
    selected_page = {"value": active_page}
    navigation = ft.ListView(expand=True, spacing=5, padding=ft.Padding.only(right=5))

    for section_name, items in NAV_SECTIONS:
        navigation.controls.append(
            ft.Container(
                content=ft.Text(section_name.upper(), size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                padding=ft.Padding.only(left=10, top=12, bottom=4),
            )
        )
        for page_id, label, icon in items:
            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, size=16, color=COLORS["accent"] if page_id == active_page else COLORS["muted"]),
                        ft.Text(label, size=12, color=COLORS["text"], expand=True),
                    ],
                    spacing=10,
                ),
                height=34,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                bgcolor=COLORS["raised"] if page_id == active_page else "transparent",
                border_radius=6,
                tooltip=label,
                on_click=lambda event, selected=page_id: on_navigate(selected),
            )
            row.on_hover = lambda event, control=row, selected=page_id: _hover_row(
                event, control, selected, selected_page["value"]
            )
            item_controls[page_id] = row
            navigation.controls.append(row)

    def set_active(page_id):
        selected_page["value"] = page_id
        for key, control in item_controls.items():
            active = key == page_id
            control.bgcolor = COLORS["raised"] if active else "transparent"
            control.content.controls[0].color = COLORS["accent"] if active else COLORS["muted"]
            try:
                control.update()
            except RuntimeError:
                pass

    brand = ft.Row(
        [
            ft.Container(width=3, height=22, bgcolor=COLORS["accent"], border_radius=2),
            ft.Column(
                [
                    ft.Text("THREATLENS", size=16, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ft.Text("SECURITY WORKSPACE", size=8, color=COLORS["muted"]),
                ],
                spacing=0,
            ),
        ],
        spacing=9,
    )

    sidebar = ft.Container(
        width=228,
        bgcolor=COLORS["sidebar"],
        padding=ft.Padding.only(left=14, top=15, right=10, bottom=10),
        border=ft.Border(right=ft.BorderSide(1, COLORS["line"])),
        content=ft.Column(
            [
                brand,
                ft.Divider(height=12, color=COLORS["line"]),
                navigation,
                ft.Divider(height=12, color=COLORS["line"]),
                ft.Row(
                    [
                        ft.CircleAvatar(content=ft.Text("TL", size=10), bgcolor=COLORS["raised"], radius=15),
                        ft.Column(
                            [
                                ft.Text("Local workspace", size=11, color=COLORS["text"]),
                                ft.Text("Operator", size=9, color=COLORS["muted"]),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.MORE_HORIZ, size=17, color=COLORS["muted"]),
                    ],
                    spacing=8,
                ),
            ],
            spacing=0,
            expand=True,
        ),
    )
    sidebar.set_active = set_active
    return sidebar


def _hover_row(event, control, page_id, active_page):
    hovering = event.data == "true"
    control.bgcolor = COLORS["raised"] if hovering or page_id == active_page else "transparent"
    try:
        control.update()
    except RuntimeError:
        pass