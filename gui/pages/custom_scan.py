import flet as ft

from ..components import COLORS, page_heading, panel, show_toast


def create_custom_scan_page(page, open_page):
    sections = {
        "DISCOVERY": [
            ("DNS Resolution", "Resolve A, AAAA, MX, NS, SOA records", True),
            ("Subdomains", "Brute-force subdomain enumeration", True),
            ("IP / Hosts", "Active host discovery and reachability", True),
            ("Ports", "Multi-worker TCP port scanning", True),
            ("Services", "Service identification and banner grab", True),
        ],
        "WEB DISCOVERY": [
            ("Crawling", "Recursive web crawler up to depth 3", True),
            ("URLs", "Extract and index all internal URLs", True),
            ("Endpoints", "Map REST and GraphQL endpoints", True),
            ("Parameters", "Fuzz hidden query and body parameters", False),
            ("APIs", "Discover OpenAPI / Swagger / schema specs", True),
            ("JavaScript", "Parse client-side JS bundles for secrets", True),
        ],
        "WEB INTELLIGENCE": [
            ("Technologies", "Wappalyzer-style stack fingerprinting", True),
            ("TLS / SSL", "Cipher suites, certificate validity, vulnerabilities", True),
            ("Security Headers", "Audit HSTS, CSP, X-Frame-Options, CORS", True),
            ("Cookies", "Verify HttpOnly, Secure, SameSite flags", True),
            ("Authentication Surface", "Identify login portals and SSO flows", True),
        ],
        "ANALYSIS": [
            ("Findings", "Correlate vulnerabilities with CVE database", True),
            ("Evidence", "Capture raw HTTP requests, responses, and traces", True),
            ("Risk Analysis", "Calculate CVSS v3.1 threat severity scores", True),
        ],
        "OUTPUT": [
            ("JSON", "Export raw machine-readable JSON telemetry", True),
            ("TXT", "Plain-text command line executive summary", True),
            ("HTML", "Interactive web report with charts", True),
            ("PDF", "Executive audit report with vulnerability details", True),
        ],
    }

    checkboxes = {}
    cards = []

    for section_title, items in sections.items():
        box_controls = []
        for label, desc, default_val in items:
            cb = ft.Checkbox(
                label=label,
                value=default_val,
                active_color=COLORS["accent"],
            )
            checkboxes[label] = cb
            box_controls.append(
                ft.Row(
                    [
                        cb,
                        ft.Text(f"({desc})", size=10, color=COLORS["muted"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ],
                    spacing=6,
                )
            )

        cards.append(
            ft.Container(
                content=panel(box_controls, title=section_title),
                col={"xs": 12, "md": 6, "xl": 4},
            )
        )

    # Advanced Controls
    timeout_input = ft.TextField(label="Timeout (seconds)", value="30", width=160, dense=True)
    scan_speed_dd = ft.Dropdown(
        label="Scan Speed Profile",
        value="Normal",
        width=180,
        dense=True,
        options=[
            ft.dropdown.Option("Stealth", "Stealth (1 req/s, IDS evasion)"),
            ft.dropdown.Option("Conservative", "Conservative (5 req/s)"),
            ft.dropdown.Option("Normal", "Normal (25 req/s)"),
            ft.dropdown.Option("Aggressive", "Aggressive (100 req/s)"),
            ft.dropdown.Option("Insane", "Insane (500 req/s, LAN only)"),
        ],
    )
    port_range_dd = ft.Dropdown(
        label="Port Range",
        value="Top 1,000 Common",
        width=200,
        dense=True,
        options=[
            ft.dropdown.Option("Top 100", "Top 100 Fast Ports"),
            ft.dropdown.Option("Top 1,000 Common", "Top 1,000 Common Ports"),
            ft.dropdown.Option("Full TCP (1-65535)", "Full TCP Range (1-65535)"),
            ft.dropdown.Option("Web Ports Only", "Web Ports (80, 443, 8080, 8443)"),
            ft.dropdown.Option("Custom", "Custom Port List"),
        ],
    )
    request_limit = ft.TextField(label="Request Limit", value="1000", width=140, dense=True)
    wordlist_input = ft.TextField(label="Wordlist Path", hint_text="Default built-in 500 words", expand=True, dense=True)

    controls_panel = panel(
        [
            ft.Row([timeout_input, scan_speed_dd, port_range_dd, request_limit], wrap=True, spacing=10),
            ft.Row([wordlist_input, ft.OutlinedButton("Browse Wordlist", icon=ft.Icons.FILE_OPEN, on_click=lambda e: show_toast(page, "Wordlist picker opened."))], spacing=10),
        ],
        title="Execution & Performance Throttling",
    )

    def apply_preset(preset_name):
        if preset_name == "all":
            for cb in checkboxes.values():
                cb.value = True
        elif preset_name == "none":
            for cb in checkboxes.values():
                cb.value = False
        elif preset_name == "network_only":
            for label, cb in checkboxes.items():
                cb.value = label in {"DNS Resolution", "Subdomains", "IP / Hosts", "Ports", "Services", "JSON", "TXT"}
        elif preset_name == "web_only":
            for label, cb in checkboxes.items():
                cb.value = label not in {"Subdomains", "IP / Hosts", "Ports"}
        page.update()
        show_toast(page, f"Preset '{preset_name.replace('_', ' ').title()}' applied.")

    preset_toolbar = ft.Row(
        [
            ft.Text("Quick Presets:", size=11, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
            ft.Chip(label=ft.Text("Select All", size=10), on_click=lambda e: apply_preset("all")),
            ft.Chip(label=ft.Text("Deselect All", size=10), on_click=lambda e: apply_preset("none")),
            ft.Chip(label=ft.Text("Network & Ports Only", size=10), on_click=lambda e: apply_preset("network_only")),
            ft.Chip(label=ft.Text("Web & Intelligence Only", size=10), on_click=lambda e: apply_preset("web_only")),
        ],
        spacing=8,
        wrap=True,
    )

    def save_profile_clicked(e):
        show_toast(page, "Custom scan configuration saved to local profile.", COLORS["lime"])

    def launch_scan_clicked(e):
        show_toast(page, "Launching Custom Scan pipeline...", COLORS["accent"])
        open_page("live_scan")

    footer_actions = ft.Row(
        [
            ft.Button("Launch Custom Scan", icon=ft.Icons.ROCKET_LAUNCH, bgcolor=COLORS["accent"], color=COLORS["canvas"], on_click=launch_scan_clicked),
            ft.Button("Save Profile", icon=ft.Icons.SAVE_OUTLINED, on_click=save_profile_clicked),
            ft.OutlinedButton("Reset Defaults", icon=ft.Icons.REPLAY, on_click=lambda e: apply_preset("all")),
        ],
        spacing=10,
    )

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading(
                    "Scan",
                    "Custom Scan Builder",
                    "Granular control over discovery engines, web crawling, vulnerability analysis, and output reports.",
                    footer_actions,
                ),
                preset_toolbar,
                controls_panel,
                ft.ResponsiveRow(cards, spacing=12, run_spacing=12),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
