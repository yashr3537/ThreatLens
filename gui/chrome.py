import flet as ft

from .components import COLORS, empty_state, severity_badge, show_toast, status_badge
from .workspace_data import (
    clear_notifications,
    get_all_notifications,
    get_all_targets,
    get_all_network,
    mark_all_notifications_read,
    search_all_data,
)
from .pages.scan_url import SCANNER_PATH, get_latest_report


def _close_dialog(event):
    event.page.pop_dialog()


def create_topbar(page, navigate):
    notifications = get_all_notifications()
    unread_count = sum(1 for n in notifications if not n.get("read"))

    notif_badge_text = ft.Text(str(unread_count), size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD)
    notif_badge = ft.Container(
        content=notif_badge_text,
        bgcolor=COLORS["red"],
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=4, vertical=1),
        visible=unread_count > 0,
    )

    def open_search(event=None):
        search_input = ft.TextField(
            hint_text="Search targets, findings, endpoints, tech, ports...",
            prefix=ft.Icon(ft.Icons.SEARCH, size=18, color=COLORS["accent"]),
            width=520,
            text_size=13,
            autofocus=True,
            border_color=COLORS["line"],
            bgcolor=COLORS["panel"],
        )
        results_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=360)

        def do_search(change_event=None):
            q = (search_input.value or "").strip()
            results_container.controls.clear()

            if not q:
                results_container.controls.append(
                    empty_state(ft.Icons.SEARCH, "Search current scan data", "Search results from targets, reports, and network inventory appear as you type.")
                )
            else:
                matches = search_all_data(q)
                if not matches:
                    results_container.controls.append(
                        empty_state(ft.Icons.SEARCH_OFF, "No matching records", f"No data matching '{q}'. Try another keyword.")
                    )
                else:
                    for category, items in matches.items():
                        cat_header = ft.Container(
                            content=ft.Text(f"{category.upper()} ({len(items)})", size=10, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
                            padding=ft.Padding.only(left=8, top=6, bottom=2),
                        )
                        results_container.controls.append(cat_header)

                        for item in items:
                            target_page = item["page"]
                            tile = ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.ARROW_RIGHT_ALT, size=15, color=COLORS["muted"]),
                                        ft.Column(
                                            [
                                                ft.Text(item["title"], size=12, color=COLORS["text"], weight=ft.FontWeight.W_500),
                                                ft.Text(item["subtitle"], size=10, color=COLORS["muted"]),
                                            ],
                                            spacing=1,
                                            expand=True,
                                        ),
                                        status_badge(category, COLORS["blue"]),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=8,
                                bgcolor=COLORS["raised"],
                                border_radius=6,
                                on_click=lambda e, pg=target_page: _select_and_navigate(pg),
                            )
                            results_container.controls.append(tile)

            if change_event:
                change_event.page.update()

        def _select_and_navigate(target_page):
            page.pop_dialog()
            navigate(target_page)

        search_input.on_change = do_search
        do_search()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.Icon(ft.Icons.TRAVEL_EXPLORE, color=COLORS["accent"], size=20),
                        ft.Text("Global ThreatLens Search", size=15, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column([search_input, ft.Divider(height=10, color=COLORS["line"]), results_container], tight=True),
                    width=580,
                    height=440,
                ),
                actions=[ft.TextButton("Close", on_click=_close_dialog)],
            )
        )

    def open_notifications(event):
        notifs = get_all_notifications()
        notif_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=320)

        def populate_notifs():
            notif_list.controls.clear()
            if not notifs:
                notif_list.controls.append(
                    empty_state(ft.Icons.NOTIFICATIONS_NONE, "No notifications", "You are completely up to date.")
                )
            else:
                for n in notifs:
                    tone = COLORS["red"] if n.get("category") == "Critical" else (COLORS["lime"] if n.get("category") == "Success" else COLORS["accent"])
                    notif_list.controls.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(width=4, height=36, bgcolor=tone, border_radius=2),
                                    ft.Column(
                                        [
                                            ft.Text(n["title"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                                            ft.Text(n["detail"], size=11, color=COLORS["muted"]),
                                            ft.Text(n["when"], size=9, color=COLORS["muted"]),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=8,
                            bgcolor=COLORS["raised"],
                            border_radius=6,
                        )
                    )

        populate_notifs()

        def on_mark_read(e):
            mark_all_notifications_read()
            notif_badge.visible = False
            page.update()
            e.page.pop_dialog()
            show_toast(page, "All notifications marked as read.")

        def on_clear(e):
            clear_notifications()
            notif_badge.visible = False
            page.update()
            e.page.pop_dialog()
            show_toast(page, "Notifications cleared.")

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.Icon(ft.Icons.NOTIFICATIONS, color=COLORS["accent"], size=20),
                        ft.Text("Notifications & Security Alerts", size=15, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(content=notif_list, width=480, height=350),
                actions=[
                    ft.TextButton("Mark All Read", on_click=on_mark_read),
                    ft.TextButton("Clear All", on_click=on_clear),
                    ft.Button("Close", on_click=_close_dialog),
                ],
            )
        )

    def open_help(event):
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.Icon(ft.Icons.HELP_OUTLINE, color=COLORS["accent"], size=20),
                        ft.Text("ThreatLens Workspace Guide", size=15, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("ThreatLens is an automated reconnaissance and cybersecurity attack surface management platform.", size=12, color=COLORS["text"]),
                            ft.Divider(height=10, color=COLORS["line"]),
                            ft.Text("WORKFLOW NAVIGATION", size=10, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
                            ft.Text("• Dashboard: High-level risk scores, module status, and recent scans.\n• Scan Center: Launch targeted reconnaissance scans.\n• Quick Scan: Run real Phase 1 multi-threaded C++ reconnaissance.\n• Live Scan: Interactive progress monitor with live terminal feed.\n• Target Explorer & Asset Graph: In-depth topology visualization.\n• Tools: 8 standalone security analyzers for DNS, TLS, Ports, Headers, etc.", size=11, color=COLORS["muted"]),
                            ft.Divider(height=10, color=COLORS["line"]),
                            ft.Text("SECURITY ENGINE STATUS", size=10, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
                            ft.Text("C++17 Engine v2.4 (Phase 1) is compiled and ready for DNS resolution, subdomain brute-force, host discovery, and multi-worker TCP port scanning.", size=11, color=COLORS["muted"]),
                        ],
                        spacing=8,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    width=500,
                    height=320,
                ),
                actions=[ft.Button("Got It", on_click=_close_dialog)],
            )
        )

    def open_profile(event):
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.CircleAvatar(content=ft.Text("OP", size=11, weight=ft.FontWeight.BOLD), bgcolor=COLORS["accent"], radius=16),
                        ft.Column(
                            [
                                ft.Text("Operator Profile", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                                ft.Text("admin@threatlens.sec · Local Workspace", size=10, color=COLORS["muted"]),
                            ],
                            spacing=1,
                        ),
                    ],
                    spacing=10,
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row([ft.Text("Role:", size=11, color=COLORS["muted"], width=100), ft.Text("Lead Security Analyst", size=11, color=COLORS["text"])]),
                            ft.Row([ft.Text("Environment:", size=11, color=COLORS["muted"], width=100), ft.Text("Windows Local / Air-Gapped", size=11, color=COLORS["text"])]),
                            ft.Row([ft.Text("C++ Scanner:", size=11, color=COLORS["muted"], width=100), status_badge("READY", COLORS["lime"])]),
                            ft.Row([ft.Text("App Version:", size=11, color=COLORS["muted"], width=100), ft.Text("ThreatLens 2.4-PRO", size=11, color=COLORS["cyan"])]),
                        ],
                        spacing=10,
                    ),
                    width=400,
                    height=140,
                ),
                actions=[ft.Button("Close", on_click=_close_dialog)],
            )
        )

    search_bar_trigger = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.SEARCH, size=15, color=COLORS["muted"]),
                ft.Text("Global search (Targets, Findings, Endpoints, Tools)...", size=11, color=COLORS["muted"], expand=True),
                ft.Container(
                    content=ft.Text("Ctrl + K", size=9, color=COLORS["muted"]),
                    bgcolor=COLORS["raised"],
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=360,
        height=34,
        padding=ft.Padding.symmetric(horizontal=12),
        bgcolor=COLORS["panel"],
        border=ft.Border.all(1, COLORS["line"]),
        border_radius=6,
        on_click=open_search,
    )

    return ft.Container(
        height=54,
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        bgcolor=COLORS["canvas"],
        border=ft.Border(bottom=ft.BorderSide(1, COLORS["line"])),
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SHIELD_OUTLINED, color=COLORS["accent"], size=20),
                        ft.Text("ThreatLens", size=16, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text("v2.4", size=9, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
                            bgcolor=f"{COLORS['accent']}18",
                            border=ft.Border.all(1, f"{COLORS['accent']}40"),
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=5, vertical=2),
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(width=16),
                ft.Container(expand=True, content=search_bar_trigger),
                ft.Stack(
                    [
                        ft.IconButton(ft.Icons.NOTIFICATIONS_OUTLINED, tooltip="Alerts & Notifications", icon_size=18, on_click=open_notifications),
                        ft.Container(content=notif_badge, right=4, top=4),
                    ],
                    alignment=ft.Alignment.TOP_RIGHT,
                ),
                ft.IconButton(ft.Icons.HELP_OUTLINE, tooltip="Documentation & Guide", icon_size=18, on_click=open_help),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, tooltip="Settings", icon_size=18, on_click=lambda e: navigate("settings")),
                ft.VerticalDivider(width=1, color=COLORS["line"]),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.CircleAvatar(content=ft.Text("TL", size=9, weight=ft.FontWeight.BOLD), bgcolor=COLORS["raised"], radius=13),
                            ft.Text("Operator", size=11, color=COLORS["text"], weight=ft.FontWeight.W_500),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                    border_radius=6,
                    tooltip="Workspace Operator",
                    on_click=open_profile,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def create_statusbar():
    scanner_ready = SCANNER_PATH.is_file()
    latest = get_latest_report()
    target_count = len(get_all_targets())
    network_count = len(get_all_network())

    active_target_label = f"Target: {latest['target']['hostname']}" if latest else "Engine Idle"

    return ft.Container(
        height=26,
        padding=ft.Padding.symmetric(horizontal=14),
        bgcolor=COLORS["sidebar"],
        border=ft.Border(top=ft.BorderSide(1, COLORS["line"])),
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(width=7, height=7, bgcolor=COLORS["lime"] if scanner_ready else COLORS["amber"], border_radius=4),
                        ft.Text("SCANNER ENGINE: READY" if scanner_ready else "SCANNER ENGINE: COMPILING", size=9, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.VerticalDivider(width=1, color=COLORS["line"]),
                ft.Text(active_target_label, size=9, color=COLORS["muted"]),
                ft.Container(expand=True),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PUBLIC, size=11, color=COLORS["muted"]),
                        ft.Text(f"{target_count} Targets", size=9, color=COLORS["muted"]),
                        ft.Container(width=8),
                        ft.Icon(ft.Icons.LAN, size=11, color=COLORS["muted"]),
                        ft.Text(f"{network_count} Open Ports", size=9, color=COLORS["muted"]),
                        ft.Container(width=8),
                        ft.Container(
                            content=ft.Text("LOCAL AIR-GAPPED", size=8, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
                            bgcolor=f"{COLORS['accent']}15",
                            padding=ft.Padding.symmetric(horizontal=5, vertical=2),
                            border_radius=3,
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )