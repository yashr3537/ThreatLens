import flet as ft

from background import create_background
from navigation import create_center
from sidebar import create_sidebar


def main(page: ft.Page):

    page.title = "ThreatLens"
    page.padding = 0

    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#00E5FF",
            on_surface="#E5F6FF",
        )
    )

    background = create_background()

    center = create_center()

    sidebar = create_sidebar(center)

    ui = ft.Column(
        [
            ft.Container(
                height=30,
                bgcolor="#0B1220",
                border=ft.Border(
                    bottom=ft.BorderSide(2, "#1E4B68")
                ),
            ),

            ft.Row(
                [
                    sidebar,
                    center,
                ],
                expand=True,
                spacing=0,
            ),
        ],
        expand=True,
        spacing=0,
    )

    page.add(
        ft.Stack(
            [
                background,
                ui,
            ],
            expand=True,
        )
    )


ft.run(main)