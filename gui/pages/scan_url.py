import flet as ft

def url_s_c(url):
    return ft.Container(
        content=ft.Text(
            f"Scanned URL: {url}",
            size=14,
            color="#AFC5D6",
        ),
    )
    

        