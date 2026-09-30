import flet as ft


def create_sidebar(center):

    sidebar = ft.Container(
        width=220,
        bgcolor="#0D1726",
        padding=20,

        border=ft.Border(
            right=ft.BorderSide(2, "#1E4B68")
        ),

        content=ft.Column(
            [
                ft.Text(
                    "THREATLENS",
                    size=27,
                    color="#00E5FF",
                    weight=ft.FontWeight.BOLD,
                ),

                ft.TextButton(
                    "🏠  Dashboard",
                    on_click=center.dashboard,
                    style=ft.ButtonStyle(
                        color="#E5F6FF",
                        bgcolor="#08111C",
                    ),
                ),

                ft.TextButton(
                    "🔍  URL Scanner",
                    on_click=center.scanner,
                    style=ft.ButtonStyle(
                        color="#E5F6FF",
                        bgcolor="#08111C",
                    ),
                ),

                ft.TextButton(
                    "📊  Reports",
                    on_click=center.reports,
                    style=ft.ButtonStyle(
                        color="#E5F6FF",
                        bgcolor="#08111C",
                    ),
                ),
            ]
        ),
    )

    def resize(e):
        sidebar.width = max(
            160,
            min(350, sidebar.width + e.local_delta.x)
        )
        sidebar.update()

    resize_bar = ft.GestureDetector(
        width=8,
        on_horizontal_drag_update=resize,
        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        content=ft.Container(),
    )

    return ft.Row(
        [
            sidebar,
            resize_bar,
        ],
        spacing=0,
    )