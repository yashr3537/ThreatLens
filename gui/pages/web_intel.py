import flet as ft

from ..components import COLORS, empty_state, page_heading, panel


def create_web_intel_page(page, open_page):
    unavailable = empty_state(
        ft.Icons.WEB,
        "Web intelligence is not connected",
        "The current Phase 1 scanner returns target, DNS, subdomain, host, and TCP port data only. It does not return HTTP headers, cookies, crawled URLs, or technologies.",
    )
    quick_links = ft.Row(
        [
            ft.OutlinedButton("HTTP Inspector", icon=ft.Icons.HTTP, on_click=lambda event: open_page("http_inspector")),
            ft.OutlinedButton("Header Analyzer", icon=ft.Icons.TEXT_SNIPPET, on_click=lambda event: open_page("header_analyzer")),
            ft.OutlinedButton("Cookie Analyzer", icon=ft.Icons.COOKIE_OUTLINED, on_click=lambda event: open_page("cookie_analyzer")),
            ft.OutlinedButton("Technology Detector", icon=ft.Icons.FINGERPRINT, on_click=lambda event: open_page("technology_detector")),
        ],
        wrap=True,
    )
    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading("Analysis", "Web intelligence", "No web analysis values are shown until a real data provider is connected."),
                panel([unavailable, quick_links], title="HTTP, headers, cookies, and technology data"),
                panel([empty_state(ft.Icons.INBOX_OUTLINED, "No web artifacts", "Crawled URLs, API endpoints, and JavaScript findings are not part of Phase 1 output.")], title="Web artifacts"),
            ],
            spacing=14,
            expand=True,
        ),
    )