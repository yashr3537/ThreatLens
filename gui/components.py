import flet as ft


COLORS = {
    "canvas": "#070C14",
    "sidebar": "#0A111D",
    "panel": "#0E1726",
    "raised": "#142033",
    "card": "#111C2E",
    "line": "#1E2F45",
    "text": "#E2E8F0",
    "muted": "#8A9BA8",
    "accent": "#20E3B2",
    "cyan": "#00E5FF",
    "blue": "#3B82F6",
    "purple": "#A855F7",
    "amber": "#F59E0B",
    "orange": "#F97316",
    "red": "#EF4444",
    "lime": "#10B981",
}


def page_heading(eyebrow, title, description, action=None):
    heading = ft.Column(
        [
            ft.Text(eyebrow.upper(), size=10, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
            ft.Text(title, size=22, color=COLORS["text"], weight=ft.FontWeight.BOLD),
            ft.Text(description, size=12, color=COLORS["muted"]),
        ],
        spacing=3,
        expand=True,
    )
    controls = [heading]
    if action is not None:
        controls.append(action)
    return ft.Row(controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def panel(content, title=None, trailing=None, padding=16, expand=False):
    children = []
    if title or trailing:
        heading = []
        if title:
            heading.append(ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=COLORS["text"]))
        if trailing:
            heading.append(trailing)
        children.append(ft.Row(heading, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    if isinstance(content, list):
        children.extend(content)
    else:
        children.append(content)
    return ft.Container(
        content=ft.Column(children, spacing=12, expand=expand),
        padding=padding,
        bgcolor=COLORS["panel"],
        border=ft.Border.all(1, COLORS["line"]),
        border_radius=8,
        expand=expand,
    )


def metric(label, value, detail, icon, tone=None):
    tone = tone or COLORS["accent"]
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label.upper(), size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(icon, size=16, color=tone),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(str(value), size=24, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                ft.Text(detail, size=10, color=COLORS["muted"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ],
            spacing=4,
        ),
        padding=14,
        bgcolor=COLORS["panel"],
        border=ft.Border.all(1, COLORS["line"]),
        border_radius=8,
        expand=True,
    )


def status_badge(label, tone=None):
    tone = tone or COLORS["lime"]
    return ft.Container(
        content=ft.Text(label.upper(), size=9, color=tone, weight=ft.FontWeight.BOLD),
        bgcolor=f"{tone}18",
        border=ft.Border.all(1, f"{tone}55"),
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
    )


def severity_badge(severity):
    sev = str(severity).lower()
    color_map = {
        "critical": COLORS["red"],
        "high": COLORS["orange"],
        "medium": COLORS["amber"],
        "low": COLORS["blue"],
        "info": COLORS["cyan"],
    }
    tone = color_map.get(sev, COLORS["muted"])
    return status_badge(severity, tone)


def tag_chip(label, on_delete=None):
    items = [ft.Text(label, size=10, color=COLORS["text"], weight=ft.FontWeight.W_500)]
    if on_delete:
        items.append(
            ft.GestureDetector(
                content=ft.Icon(ft.Icons.CLOSE, size=11, color=COLORS["muted"]),
                on_tap=on_delete,
            )
        )
    return ft.Container(
        content=ft.Row(items, spacing=4, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=COLORS["raised"],
        border=ft.Border.all(1, COLORS["line"]),
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
    )


def section_label(label):
    return ft.Text(label.upper(), size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD)


def show_toast(page, message, tone=None):
    tone = tone or COLORS["accent"]
    snack = ft.SnackBar(
        content=ft.Text(message, size=12, color=tone),
        bgcolor=COLORS["raised"],
        duration=2500,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


def show_notice(page, message, title="ThreatLens Notice"):
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
            content=ft.Text(message, size=12, color=COLORS["muted"]),
            actions=[ft.TextButton("Close", on_click=lambda event: page.pop_dialog())],
        )
    )


def empty_state(icon, title, description, action=None):
    controls = [
        ft.Icon(icon, size=28, color=COLORS["muted"]),
        ft.Text(title, size=14, color=COLORS["text"], weight=ft.FontWeight.BOLD),
        ft.Text(description, size=11, color=COLORS["muted"], text_align=ft.TextAlign.CENTER),
    ]
    if action:
        controls.append(ft.Container(height=4))
        controls.append(action)
    return ft.Container(
        content=ft.Column(
            controls,
            spacing=7,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=28,
        alignment=ft.Alignment.CENTER,
    )