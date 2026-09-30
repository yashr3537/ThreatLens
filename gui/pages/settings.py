import flet as ft

from ..components import COLORS, page_heading, panel, show_toast, status_badge
from ..workspace_data import get_settings, update_settings


def create_settings_page(page, open_page):
    current = get_settings()

    # GENERAL
    startup_dd = ft.Dropdown(
        label="Startup Page",
        value=current.get("startup_page", "dashboard").title(),
        options=[ft.dropdown.Option(opt) for opt in ["Dashboard", "Scan Center", "Targets", "Findings"]],
    )
    notif_switch = ft.Switch(label="Desktop Security Notifications", value=current.get("notifications", True), active_color=COLORS["accent"])
    autosave_switch = ft.Switch(label="Auto-save Session State", value=current.get("auto_save", True), active_color=COLORS["accent"])
    confirm_del_switch = ft.Switch(label="Confirm Before Deletion", value=current.get("confirm_delete", True), active_color=COLORS["accent"])

    general_panel = panel(
        [
            startup_dd,
            notif_switch,
            autosave_switch,
            confirm_del_switch,
        ],
        title="General Configuration",
    )

    # SCANNER
    timeout_input = ft.TextField(label="Socket Timeout (ms)", value=current.get("timeout", "500"), width=180)
    concurrency_input = ft.TextField(label="Worker Concurrency", value=current.get("concurrency", "16"), width=180)
    port_range_dd = ft.Dropdown(
        label="Default Port Scope",
        value="Top 1,000 Common",
        options=[ft.dropdown.Option(opt) for opt in ["Top 100", "Top 1,000 Common", "Full TCP (1-65535)", "Web Ports (80/443)"]],
    )
    wordlist_input = ft.TextField(label="Default Wordlist Path", hint_text="C:\\ThreatLens\\wordlists\\subdomains-500.txt", expand=True)
    scan_speed_dd = ft.Dropdown(
        label="Scan Speed Profile",
        value=current.get("scan_speed", "Normal"),
        options=[ft.dropdown.Option(opt) for opt in ["Stealth", "Conservative", "Normal", "Aggressive"]],
    )

    scanner_panel = panel(
        [
            ft.Row([timeout_input, concurrency_input, scan_speed_dd], wrap=True, spacing=10),
            port_range_dd,
            wordlist_input,
        ],
        title="C++ Scanner Engine Defaults",
    )

    # OUTPUT
    default_fmt_dd = ft.Dropdown(
        label="Default Export Format",
        value=current.get("default_format", "PDF"),
        options=[ft.dropdown.Option(opt) for opt in ["PDF", "JSON", "HTML", "TXT"]],
    )
    report_loc = ft.TextField(label="Report Output Location", value="C:\\ThreatLens\\reports\\", expand=True)
    evidence_loc = ft.TextField(label="Evidence Storage Location", value="C:\\ThreatLens\\evidence\\", expand=True)

    output_panel = panel(
        [
            default_fmt_dd,
            report_loc,
            evidence_loc,
        ],
        title="Report & Evidence Storage",
    )

    # APPEARANCE
    theme_dd = ft.Dropdown(
        label="Color Theme",
        value=current.get("theme", "Dark Cybersecurity"),
        options=[ft.dropdown.Option(opt) for opt in ["Dark Cybersecurity", "Midnight Blue", "High Contrast Stealth"]],
    )
    compact_switch = ft.Switch(label="Compact Layout Density", value=current.get("compact", False), active_color=COLORS["accent"])
    anim_switch = ft.Switch(label="Enable UI Animations", value=current.get("animations", True), active_color=COLORS["accent"])
    bg_style_dd = ft.Dropdown(
        label="Canvas Background Style",
        value="Subtle Grid",
        options=[ft.dropdown.Option(opt) for opt in ["Subtle Grid", "Deep Solid", "Cyber Dots"]],
    )

    appearance_panel = panel(
        [
            ft.Row([theme_dd, bg_style_dd], wrap=True, spacing=10),
            ft.Row([compact_switch, anim_switch], wrap=True, spacing=10),
        ],
        title="Appearance & Interface",
    )

    # MODULES
    module_names = [
        "DNS Intelligence",
        "Subdomain Discovery",
        "Host & IP Discovery",
        "Port Scanner (TCP/UDP)",
        "Web Engine & Crawler",
        "TLS / SSL Auditor",
        "Security Header Analyzer",
        "Technology Fingerprinter",
        "Report Engine",
    ]
    module_switches = []
    for m in module_names:
        module_switches.append(
            ft.Row(
                [
                    ft.Text(m, size=11, color=COLORS["text"], expand=True),
                    ft.Switch(value=True, active_color=COLORS["accent"]),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    modules_panel = panel(module_switches, title="Modular Reconnaissance Engines")

    def save_settings_click(e):
        update_settings({
            "startup_page": startup_dd.value.lower(),
            "notifications": notif_switch.value,
            "auto_save": autosave_switch.value,
            "confirm_delete": confirm_del_switch.value,
            "timeout": timeout_input.value,
            "concurrency": concurrency_input.value,
            "scan_speed": scan_speed_dd.value,
            "default_format": default_fmt_dd.value,
            "theme": theme_dd.value,
            "compact": compact_switch.value,
            "animations": anim_switch.value,
        })
        show_toast(page, "Settings saved successfully to session profile.", COLORS["lime"])

    def reset_settings_click(e):
        show_toast(page, "Settings reset to factory defaults.")

    actions_bar = ft.Row(
        [
            ft.Button("Save Settings", icon=ft.Icons.SAVE, bgcolor=COLORS["accent"], color=COLORS["canvas"], on_click=save_settings_click),
            ft.OutlinedButton("Reset Defaults", icon=ft.Icons.REPLAY, on_click=reset_settings_click),
        ],
        spacing=10,
    )

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading(
                    "System",
                    "Global Preferences & Settings",
                    "Configure scanner performance parameters, modular reconnaissance engines, output storage, and UI appearance.",
                    actions_bar,
                ),
                ft.ResponsiveRow(
                    [
                        ft.Container(content=general_panel, col={"xs": 12, "lg": 6}),
                        ft.Container(content=scanner_panel, col={"xs": 12, "lg": 6}),
                        ft.Container(content=output_panel, col={"xs": 12, "lg": 6}),
                        ft.Container(content=appearance_panel, col={"xs": 12, "lg": 6}),
                        ft.Container(content=modules_panel, col={"xs": 12, "lg": 12}),
                    ],
                    spacing=12,
                    run_spacing=12,
                ),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
