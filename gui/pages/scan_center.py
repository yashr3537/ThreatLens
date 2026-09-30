import flet as ft

from ..components import COLORS, page_heading, panel, show_toast, status_badge
from ..workspace_data import add_target
from ..scan_config import SUPPORTED_MODULES
from .scan_url import get_latest_report, run_phase1_scan


def create_scan_center_page(page, open_page):
    latest = get_latest_report()
    default_target = latest["target"]["input"] if latest else ""

    target_input = ft.TextField(
        label="Target URL or Domain",
        value=default_target,
        hint_text="Enter a URL/domain you are authorized to assess",
        prefix=ft.Icon(ft.Icons.LANGUAGE, size=18, color=COLORS["accent"]),
        expand=True,
    )

    auth_checkbox = ft.Checkbox(
        label="I confirm I am authorized to scan and assess this target",
        value=False,
        active_color=COLORS["accent"],
    )

    profile_dropdown = ft.Dropdown(
        label="Scan Profile",
        value="Standard Scan",
        width=220,
        options=[
            ft.dropdown.Option("Quick Scan", "Quick (smaller DNS list)"),
            ft.dropdown.Option("Standard Scan", "Standard (recommended)"),
        ],
    )

    status_message = ft.Text("Ready to initiate security assessment.", size=12, color=COLORS["muted"])
    scan_progress = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)

    module_controls = {
        "target_profile": ft.Checkbox(label="Target Profile (required)", value=True, disabled=True, active_color=COLORS["accent"]),
        "dns": ft.Checkbox(label="DNS Intelligence", value=True, active_color=COLORS["accent"]),
        "hosts": ft.Checkbox(label="Host / IP Discovery", value=True, active_color=COLORS["accent"]),
        "subdomains": ft.Checkbox(label="Subdomain Intelligence", value=True, active_color=COLORS["accent"]),
        "ports": ft.Checkbox(label="Port Discovery", value=True, active_color=COLORS["accent"]),
        "services": ft.Checkbox(label="Service Detection", value=True, active_color=COLORS["accent"]),
        "dns_records": ft.Checkbox(label="DNS Records (CNAME/MX/NS/TXT)", value=False, active_color=COLORS["accent"]),
        "http_probe": ft.Checkbox(label="HTTP Information", value=False, active_color=COLORS["accent"]),
        "url_probe": ft.Checkbox(label="URL Probe", value=False, active_color=COLORS["accent"]),
        "endpoints": ft.Checkbox(label="Endpoint / API Discovery", value=False, active_color=COLORS["accent"]),
        "directory": ft.Checkbox(label="Directory Discovery", value=False, active_color=COLORS["accent"]),
        "tls": ft.Checkbox(label="TLS Inspector", value=False, active_color=COLORS["accent"]),
        "headers": ft.Checkbox(label="Security Headers", value=False, active_color=COLORS["accent"]),
        "cookies": ft.Checkbox(label="Cookie Inspector", value=False, active_color=COLORS["accent"]),
        "technology": ft.Checkbox(label="Technology Intelligence", value=False, active_color=COLORS["accent"]),
    }
    coming_soon_modules = [
        ft.Checkbox(label=f"{label} · COMING SOON", value=False, disabled=True)
        for label in ("Vulnerability analysis", "Source code analysis", "Dependency analysis", "Container analysis")
    ]

    port_mode = ft.Dropdown(
        label="TCP port scope",
        value="common",
        width=200,
        options=[ft.dropdown.Option("common", "Common ports"), ft.dropdown.Option("list", "Custom list"), ft.dropdown.Option("full", "Full TCP range")],
    )
    ports_field = ft.TextField(label="Ports, comma-separated", hint_text="22,80,443", width=220, visible=False)
    confirm_full_range = ft.Checkbox(label="Confirm full-range scan (1-65535)", value=False, visible=False)
    wordlist_field = ft.TextField(label="Subdomain wordlist (optional)", hint_text="One label per line", expand=True)
    directory_wordlist_field = ft.TextField(label="Directory wordlist (required when selected)", hint_text="One relative path per line", expand=True, visible=False)
    max_candidates_field = ft.TextField(label="DNS candidate limit", value="500", width=170)
    dns_delay_field = ft.TextField(label="DNS delay (ms)", value="100", width=150)
    timeout_field = ft.TextField(label="Port timeout (ms)", value="500", width=160)
    concurrency_field = ft.TextField(label="Port workers", value="8", width=140)
    advanced_options = ft.Container(visible=False)

    def update_port_mode(event):
        ports_field.visible = port_mode.value == "list"
        confirm_full_range.visible = port_mode.value == "full"
        event.page.update()

    def update_service_dependency(event):
        module_controls["services"].disabled = not module_controls["ports"].value
        if module_controls["services"].disabled:
            module_controls["services"].value = False
        event.page.update()

    port_mode.on_change = update_port_mode
    module_controls["ports"].on_change = update_service_dependency

    def update_directory_wordlist(event):
        directory_wordlist_field.visible = bool(module_controls["directory"].value)
        event.page.update()

    module_controls["directory"].on_change = update_directory_wordlist

    def toggle_advanced(event):
        advanced_options.visible = not advanced_options.visible
        event.control.text = "Hide advanced options" if advanced_options.visible else "Advanced options"
        event.page.update()

    advanced_button = ft.TextButton("Advanced options", icon=ft.Icons.TUNE, on_click=toggle_advanced)
    advanced_options.content = panel(
        [
            ft.Row([port_mode, ports_field, confirm_full_range], wrap=True),
            wordlist_field,
            directory_wordlist_field,
            ft.Row([max_candidates_field, dns_delay_field, timeout_field, concurrency_field], wrap=True),
            ft.Text("Limits: DNS 50-5000 ms, TCP timeout 100-10000 ms, workers 1-32, candidates 1-10000.", size=10, color=COLORS["muted"]),
        ],
        title="Advanced scan bounds",
    )

    # Config preview values
    concurrency_text = ft.Text("8 Workers", size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD)
    timeout_text = ft.Text("500 ms", size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD)
    port_scope_text = ft.Text("Common TCP Ports", size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD)

    def on_profile_change(e):
        p = profile_dropdown.value
        if p == "Quick Scan":
            concurrency_text.value = "4 Workers"
            timeout_text.value = "300 ms"
            port_scope_text.value = "Common TCP Ports"
        elif p == "Standard Scan":
            concurrency_text.value = "8 Workers"
            timeout_text.value = "500 ms"
            port_scope_text.value = "Common TCP Ports"
        page.update()

    profile_dropdown.on_change = on_profile_change

    async def start_scan_clicked(e):
        target_val = (target_input.value or "").strip()
        if not target_val:
            show_toast(page, "Please enter a valid target URL or domain.", COLORS["red"])
            return
        if not auth_checkbox.value:
            show_toast(page, "Authorization confirmation is required.", COLORS["amber"])
            return

        modules = frozenset(key for key, control in module_controls.items() if control.value)
        try:
            candidates = int(max_candidates_field.value or "500")
            dns_delay = int(dns_delay_field.value or "100")
            timeout = int(timeout_field.value or "500")
            concurrency = int(concurrency_field.value or "8")
        except ValueError:
            status_message.value = "Advanced limits must be whole numbers."
            page.update()
            return
        selected_port_mode = (port_mode.value or "common") if "ports" in modules else "common"
        if "ports" in modules and selected_port_mode == "full" and not confirm_full_range.value:
            status_message.value = "Confirm the full TCP range before scanning."
            page.update()
            return
        if "ports" in modules and selected_port_mode == "list" and not (ports_field.value or "").strip():
            status_message.value = "Enter a port list or choose Common ports."
            page.update()
            return

        start_button.disabled = True
        scan_progress.visible = True
        status_message.value = f"Scanning {target_val}..."
        page.update()
        try:
            await run_phase1_scan(
                target_val,
                authorized=True,
                modules=modules,
                wordlist_path=wordlist_field.value or "",
                max_candidates=candidates,
                dns_delay_ms=dns_delay,
                port_mode=selected_port_mode,
                ports=ports_field.value or "",
                timeout_ms=timeout,
                concurrency=concurrency,
                full_range_confirmed=bool(confirm_full_range.value),
                directory_wordlist_path=directory_wordlist_field.value or "",
            )
            add_target(target_val, "URL / domain")
            status_message.value = "Phase 1 scan completed."
            show_toast(page, f"Scan completed for {target_val}.", COLORS["lime"])
            open_page("live_scan")
        except Exception as error:
            status_message.value = str(error)
        finally:
            start_button.disabled = False
            scan_progress.visible = False
            page.update()

    def stop_scan_clicked(e):
        status_message.value = "Scan halted by operator."
        show_toast(page, "Scan stopped.", COLORS["amber"])
        page.update()

    def pause_scan_clicked(e):
        status_message.value = "Scan paused."
        show_toast(page, "Scan paused.", COLORS["blue"])
        page.update()

    def clear_clicked(e):
        target_input.value = ""
        auth_checkbox.value = False
        status_message.value = "Fields cleared."
        page.update()

    # Preset shortcut pills
    def set_target(val):
        target_input.value = val
        page.update()

    start_button = ft.Button("Start Scan", icon=ft.Icons.PLAY_ARROW, bgcolor=COLORS["accent"], color=COLORS["canvas"], on_click=start_scan_clicked)
    action_buttons = ft.Row(
        [
            start_button,
            ft.OutlinedButton("Pause", icon=ft.Icons.PAUSE, disabled=True, tooltip="The scanner does not currently support pausing."),
            ft.OutlinedButton("Stop", icon=ft.Icons.STOP, disabled=True, tooltip="The scanner currently completes as a single process."),
            ft.TextButton("Clear", icon=ft.Icons.CLEAR_ALL, on_click=clear_clicked),
            ft.Container(expand=True),
            scan_progress,
            status_message,
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    target_panel = panel(
        [
            ft.Row([target_input, profile_dropdown], spacing=10),
            auth_checkbox,
            ft.Text("Target and network modules", size=10, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
            ft.Row([module_controls[key] for key in ("target_profile", "dns", "hosts", "subdomains", "ports", "services")], wrap=True),
            ft.Text("Available providers", size=10, color=COLORS["accent"], weight=ft.FontWeight.BOLD),
                ft.Row([module_controls[key] for key in ("dns_records", "http_probe", "url_probe", "endpoints", "directory", "tls", "headers", "cookies", "technology") if key in SUPPORTED_MODULES], wrap=True),
            ft.Text("Planned providers", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
            ft.Row(coming_soon_modules, wrap=True),
            advanced_button,
            advanced_options,
            action_buttons,
        ],
        title="Target & Profile Configuration",
    )

    config_card = panel(
        [
            ft.Row([ft.Text("Concurrency:", size=11, color=COLORS["muted"], width=120), concurrency_text]),
            ft.Row([ft.Text("Socket Timeout:", size=11, color=COLORS["muted"], width=120), timeout_text]),
            ft.Row([ft.Text("Port Range:", size=11, color=COLORS["muted"], width=120), port_scope_text]),
            ft.Row([ft.Text("Subdomain candidates:", size=11, color=COLORS["muted"], width=120), ft.Text("500 paced DNS lookups by default", size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD)]),
            ft.Row([ft.Text("Connected modules:", size=11, color=COLORS["muted"], width=120), ft.Text("Target, DNS, subdomain, host, TCP ports", size=12, color=COLORS["accent"], weight=ft.FontWeight.BOLD)]),
        ],
        title="Active Scan Profile Parameters",
    )

    pipeline_stages = [
        ("Target profile", "Parses the provided URL and hostname", "AVAILABLE", COLORS["lime"]),
        ("DNS intelligence", "Resolves IPv4 and IPv6 addresses", "AVAILABLE", COLORS["lime"]),
        ("Subdomain discovery", "Uses configured wordlist with paced DNS queries", "AVAILABLE", COLORS["lime"]),
        ("Host inventory", "Stores resolved target and subdomain addresses", "AVAILABLE", COLORS["lime"]),
        ("TCP port inventory", "Checks selected TCP ports and safe banners", "AVAILABLE", COLORS["lime"]),
        ("Web discovery", "Not connected to the current scanner", "NOT CONNECTED", COLORS["muted"]),
        ("Finding analysis", "Not connected to the current scanner", "NOT CONNECTED", COLORS["muted"]),
    ]

    pipeline_rows = [
        ft.Row(
            [
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE if status == "AVAILABLE" else ft.Icons.RADIO_BUTTON_UNCHECKED, size=16, color=tone),
                ft.Column(
                    [
                        ft.Text(name, size=11, color=COLORS["text"], weight=ft.FontWeight.BOLD),
                        ft.Text(desc, size=10, color=COLORS["muted"]),
                    ],
                    spacing=1,
                    expand=True,
                ),
                status_badge(status, tone),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        for name, desc, status, tone in pipeline_stages
    ]

    pipeline_panel = panel(pipeline_rows, title="Reconnaissance Execution Pipeline")

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading(
                    "Scan",
                    "Scan Center",
                    "Configure, initiate, and monitor targeted reconnaissance scans across your authorized attack surface.",
                    ft.Button("Custom Scan Config", icon=ft.Icons.TUNE, on_click=lambda e: open_page("custom_scan")),
                ),
                target_panel,
                ft.ResponsiveRow(
                    [
                        ft.Container(content=config_card, col={"xs": 12, "lg": 5}),
                        ft.Container(content=pipeline_panel, col={"xs": 12, "lg": 7}),
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
