import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, show_toast
from .scan_url import run_phase1_scan


TOOL_CONFIGS = {
    "dns_lookup": ("DNS Intelligence", "Resolve actual A/AAAA/CNAME/MX/NS/TXT records with bounded resolver timeouts."),
    "port_scanner": ("Network Discovery", "Use the existing C++ IPv4/IPv6 TCP inventory with bounded timeout and concurrency."),
    "http_inspector": ("HTTP Inspector", "Inspect a bounded real response, status, headers, redirect chain, and content type."),
    "tls_inspector": ("TLS Inspector", "Inspect a verified TLS certificate and negotiated protocol/cipher."),
    "header_analyzer": ("Security Header Inspector", "Report actual security headers as present or missing; no severity is invented."),
    "cookie_analyzer": ("Cookie Inspector", "Inspect attributes from actual Set-Cookie response headers without storing values."),
    "technology_detector": ("Technology Intelligence", "Identify technologies only from observed response header/body evidence."),
    "url_analyzer": ("URL Probe", "Check actual HTTP status, title, content type, redirects, and response timing."),
}

TOOL_MODULES = {
    "dns_lookup": {"target_profile", "dns", "dns_records"},
    "port_scanner": {"target_profile", "hosts", "ports", "services"},
    "http_inspector": {"target_profile", "http_probe"},
    "tls_inspector": {"target_profile", "tls"},
    "header_analyzer": {"target_profile", "headers"},
    "cookie_analyzer": {"target_profile", "cookies"},
    "technology_detector": {"target_profile", "technology"},
    "url_analyzer": {"target_profile", "url_probe"},
}


def create_tool_page(page, tool_id, open_page):
    title, description = TOOL_CONFIGS[tool_id]
    target = ft.TextField(label="Target URL or hostname", hint_text="Enter an authorized target", expand=True)
    authorized = ft.Checkbox(label="I own this target or have permission to assess it", value=False)
    port_mode = ft.Dropdown(
        label="Port selection",
        value="common",
        width=190,
        options=[ft.dropdown.Option("common", "Common ports"), ft.dropdown.Option("list", "Custom list"), ft.dropdown.Option("full", "Full TCP range")],
        visible=tool_id == "port_scanner",
    )
    ports = ft.TextField(label="Ports, comma-separated", hint_text="22,80,443", visible=False, width=220)
    confirm_full = ft.Checkbox(label="Confirm full TCP range", value=False, visible=False)
    status = ft.Text(size=11, color=COLORS["muted"])
    output = ft.Container(content=empty_state(ft.Icons.INBOX_OUTLINED, "No results", "Run a connected Phase 1 tool or wait for its backend to be implemented."), expand=True)
    progress = ft.ProgressRing(visible=False, width=18, height=18)
    run_button = ft.Button("Run", icon=ft.Icons.PLAY_ARROW)

    def update_mode(event):
        ports.visible = port_mode.value == "list"
        confirm_full.visible = port_mode.value == "full"
        event.page.update()

    port_mode.on_change = update_mode

    def render_phase1(data):
        if tool_id == "dns_lookup":
            dns = data["dns"]
            rows = [ft.Text(f"DNS status: {dns['status']} · {dns['message']}", size=12, color=COLORS["text"])]
            rows.extend(ft.Text(f"Address: {address}", size=12, color=COLORS["text"], selectable=True) for address in dns["addresses"])
            record_result = data.get("tool_results", {}).get("dns_records", {})
            for record in record_result.get("data", {}).get("records", []):
                rows.append(ft.Text(f"{record['type']} · {record['name']} · TTL {record['ttl']} · {record['value']}", size=11, color=COLORS["text"], selectable=True))
            rows.extend(ft.Text(f"DNS error: {error}", size=10, color=COLORS["amber"]) for error in record_result.get("errors", []))
            output.content = panel(rows or [empty_state(ft.Icons.DNS, "No DNS records", "The scanner returned no resolving addresses.")], title="Real DNS results")
        elif tool_id == "port_scanner":
            rows = [
                ft.Text(f"{item['address']} · {item['port']}/{item['protocol']} · {item['state']} · {item['service']} · {item['version'] or 'version unavailable'}", size=12, color=COLORS["text"], selectable=True)
                for item in data["ports"]
            ]
            output.content = panel(rows or [empty_state(ft.Icons.LAN, "No open ports", "No open TCP ports were returned by this scan.")], title="Real TCP results")
        else:
            result = data.get("tool_results", {}).get(next(iter(TOOL_MODULES[tool_id] - {"target_profile"}), ""))
            if not result:
                output.content = empty_state(ft.Icons.INBOX_OUTLINED, "No provider result", "This selected provider returned no result object.")
                return
            result_rows = [status_badge(result.get("status", "unknown"), COLORS["lime"] if result.get("status") == "completed" else COLORS["amber"])]
            for key, value in result.get("data", {}).items():
                if key in {"body_preview", "records", "cookies", "headers", "detections", "endpoints", "javascript", "redirects", "matches"}:
                    result_rows.append(ft.Text(f"{key.replace('_', ' ').title()}: {value}", size=10, color=COLORS["text"], selectable=True))
                else:
                    result_rows.append(ft.Text(f"{key.replace('_', ' ').title()}: {value}", size=11, color=COLORS["text"], selectable=True))
            result_rows.extend(ft.Text(f"Error: {error}", size=10, color=COLORS["amber"]) for error in result.get("errors", []))
            output.content = panel(result_rows, title=f"Real {title} result")

    async def run_tool(event):
        if not authorized.value:
            status.value = "Confirm authorization before scanning."
            event.page.update()
            return
        if not (target.value or "").strip():
            status.value = "Enter a target first."
            event.page.update()
            return
        if tool_id == "port_scanner" and port_mode.value == "full" and not confirm_full.value:
            status.value = "Confirm the full TCP range first."
            event.page.update()
            return
        if tool_id == "port_scanner" and port_mode.value == "list" and not (ports.value or "").strip():
            status.value = "Enter a comma-separated port list."
            event.page.update()
            return

        target_value = (target.value or "").strip()
        if "://" not in target_value:
            target_value = "https://" + target_value

        run_button.disabled = True
        progress.visible = True
        status.value = "Running the real Phase 1 scanner..."
        event.page.update()
        try:
            data = await run_phase1_scan(
                target_value,
                authorized=True,
                modules=TOOL_MODULES[tool_id],
                history_kind="tool",
                port_mode=port_mode.value if tool_id == "port_scanner" else "common",
                ports=ports.value or "",
                full_range_confirmed=bool(confirm_full.value),
            )
            render_phase1(data)
            status.value = "Real scanner results loaded."
            show_toast(page, "Phase 1 scan completed.", COLORS["lime"])
        except Exception as error:
            status.value = str(error)
        finally:
            run_button.disabled = False
            progress.visible = False
            event.page.update()

    run_button.on_click = run_tool
    controls = [target, authorized]
    if tool_id == "port_scanner":
        controls.append(ft.Row([port_mode, ports, confirm_full], wrap=True))
    controls.extend([ft.Row([run_button, progress, status], wrap=True), output])

    tool_links = [
        (key, label)
        for key, (label, _) in TOOL_CONFIGS.items()
        if key != tool_id
    ]
    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading("Tools", title, description),
                ft.Row([ft.TextButton(label, on_click=lambda event, selected=key: open_page(selected)) for key, label in tool_links], wrap=True),
                panel(controls[:-1], title="Configuration"),
                controls[-1],
            ],
            spacing=14,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
    )