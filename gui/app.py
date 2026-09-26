import flet as ft


def main(page: ft.Page):

    page.title = "ThreatLens"
    page.padding = 0
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#00E5FF",
            on_surface="#E5F6FF",
        )
    )

    # BACKGROUND
    background = ft.Container(
        expand=True,
        bgcolor="#05070D",
    )

    # NAVBAR
    navbar = ft.Container(
        height=30,
        bgcolor="#0B1220",
        border=ft.Border(
            bottom=ft.BorderSide(2, "#1E4B68")
        ),
    )

    # SIDEBAR
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
                
                style=ft.ButtonStyle(
                    color="#E5F6FF",
                    bgcolor="#08111C",
                ),
            ),
            ft.TextButton(
                "🔍  URL Scanner",
                style=ft.ButtonStyle(
                    color="#E5F6FF",
                    bgcolor="#08111C",
                ),
            ),
            
            ft.TextButton(
                "📊  Reports",
                style=ft.ButtonStyle(
                    color="#E5F6FF",
                    bgcolor="#08111C",
                ),
            ),
        ]
    ),
)

    # SIDEBAR RESIZE
    def resize(e):
        sidebar.width = max(160, min(350, sidebar.width + e.local_delta.x))
        sidebar.update()

    resize_bar = ft.GestureDetector(
        width=8,
        on_horizontal_drag_update=resize,
        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        content=ft.Container(
            bgcolor="transparent"
        
        ),
    )

    # CENTER
    center = ft.Container(
        expand=True,
        bgcolor="#08111C",
    )

    # MAIN LAYOUT
    ui = ft.Column(
        [
            navbar,

            ft.Row(
                [
                    sidebar,
                    resize_bar,
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