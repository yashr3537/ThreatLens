import sys
from pathlib import Path

# Ensure gui directory and project root are in sys.path
GUI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = GUI_DIR.parent
if str(GUI_DIR) not in sys.path:
    sys.path.insert(0, str(GUI_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import flet as ft

from gui.chrome import create_statusbar, create_topbar
from gui.components import COLORS
from gui.background import create_background
from gui.navigation import create_center
from gui.sidebar import create_sidebar


def main(page: ft.Page):

    page.title = "ThreatLens"
    page.padding = 0
    page.bgcolor = COLORS["canvas"]
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(font_family="Aptos", color_scheme=ft.ColorScheme(primary=COLORS["accent"], on_surface=COLORS["text"]))
    page.window.width = 1440
    page.window.height = 900
    page.window.min_width = 1040
    page.window.min_height = 680

    background = create_background()
    center = create_center(page)
    sidebar = create_sidebar(center.navigate)
    center.set_sidebar(sidebar)
    topbar = create_topbar(page, center.navigate)
    statusbar = create_statusbar()
    workspace = ft.Column(
        [
            topbar,
            ft.Row([sidebar, center], expand=True, spacing=0),
            statusbar,
        ],
        expand=True,
        spacing=0,
    )

    page.add(
        ft.Stack(
            [background, workspace],
            expand=True,
        )
    )


ft.run(main)