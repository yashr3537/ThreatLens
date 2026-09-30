import flet as ft
from pages.single_input import create_single_input_page


def create_center():

    center = ft.Container(
        expand=True,
        bgcolor="#08111C",
    )

    def dashboard(e):
        center.content = ft.Text(
            "DASHBOARD",
            size=30,
            color="#00E5FF",
        )
        center.update()

    def scanner(e):
        center.content = ft.Container(
            padding=30,
            content=ft.Column(
                [
                    ft.Text(
                        "URL Scanner",
                        size=30,
                        color="#00E5FF",
                        weight=ft.FontWeight.BOLD,
                    ),

                    ft.Text(
                        "Choose a scanning option",
                        size=16,
                        color="#AFC5D6",
                    ),

                    ft.TextButton(
                        "🔗  Scan Single URL",
                        on_click=lambda e: setattr(center, "content", create_single_input_page()),
                        style=ft.ButtonStyle(
                            color="#E5F6FF",
                            bgcolor="#08111C",
                        ),
                    ),

                    ft.TextButton(
                        "📄  Scan Multiple URLs",
                        style=ft.ButtonStyle(
                            color="#E5F6FF",
                            bgcolor="#08111C",
                        ),
                    ),

                    ft.TextButton(
                        "📁  Import URLs from File",
                        style=ft.ButtonStyle(
                            color="#E5F6FF",
                            bgcolor="#08111C",
                        ),
                    ),
                ]
            ),
        )

        center.update()

    def reports(e):
        center.content = ft.Text(
            "REPORTS",
            size=30,
            color="#00E5FF",
        )
        center.update()

    center.dashboard = dashboard
    center.scanner = scanner
    center.reports = reports

    return center