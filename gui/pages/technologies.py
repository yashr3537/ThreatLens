import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, show_toast, status_badge
from ..workspace_data import get_all_technologies


def create_technologies_page(page, open_page):
    search_input = ft.TextField(
        hint_text="Search technologies or signatures...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=260,
        dense=True,
    )
    category_filter = ft.Dropdown(
        label="Category",
        value="All",
        width=160,
        dense=True,
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(c) for c in ["Server", "Framework", "JavaScript", "Database", "CDN", "Hosting", "CMS"]],
    )

    cards_container = ft.Container(expand=True)
    count_text = ft.Text(size=11, color=COLORS["muted"])

    def render_tech(e=None):
        q = (search_input.value or "").strip().lower()
        cat = category_filter.value

        all_tech = get_all_technologies(category=cat, search=q)
        count_text.value = f"{len(all_tech)} components fingerprinted"

        if not all_tech:
            cards_container.content = empty_state(
                ft.Icons.FINGERPRINT,
                "No technologies match filter",
                "Try adjusting your search query or selecting 'All' categories.",
            )
        else:
            cards = []
            for t in all_tech:
                cat_tone = {
                    "Server": COLORS["blue"],
                    "Framework": COLORS["purple"],
                    "JavaScript": COLORS["cyan"],
                    "Database": COLORS["amber"],
                    "CDN": COLORS["lime"],
                    "Hosting": COLORS["orange"],
                    "CMS": COLORS["accent"],
                }.get(t["category"], COLORS["muted"])

                card = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(ft.Icons.MEMORY, size=18, color=cat_tone),
                                            ft.Text(t["technology"], size=13, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                                        ],
                                        spacing=8,
                                    ),
                                    status_badge(f"{t['confidence']} MATCH", COLORS["lime"]),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    status_badge(t["category"], cat_tone),
                                    ft.Text(t.get("target", "General"), size=10, color=COLORS["muted"]),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Divider(height=6, color=COLORS["line"]),
                            ft.Text("FINGERPRINT EVIDENCE", size=9, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Text(t["evidence"], size=10, font_family="Consolas, Courier", color=COLORS["text"], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                bgcolor="#05080E",
                                padding=6,
                                border_radius=4,
                                border=ft.Border.all(1, COLORS["line"]),
                            ),
                        ],
                        spacing=6,
                    ),
                    padding=12,
                    bgcolor=COLORS["panel"],
                    border=ft.Border.all(1, COLORS["line"]),
                    border_radius=8,
                    col={"xs": 12, "sm": 6, "lg": 4},
                )
                cards.append(card)

            cards_container.content = ft.ResponsiveRow(cards, spacing=10, run_spacing=10)

        if e:
            page.update()

    search_input.on_change = render_tech
    category_filter.on_change = render_tech
    render_tech()

    toolbar = ft.Row(
        [
            search_input,
            category_filter,
            ft.Container(expand=True),
            count_text,
            ft.Button("Fingerprint Target", icon=ft.Icons.RADAR, on_click=lambda e: open_page("technology_detector")),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh Technologies", on_click=render_tech),
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
                    "Technology Fingerprinting",
                    "Automated identification of backend web servers, application frameworks, front-end libraries, databases, and CDN providers.",
                ),
                panel([toolbar, cards_container], title="Identified Technology Stack", expand=True),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
