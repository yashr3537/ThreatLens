from datetime import datetime
from html import escape
from io import BytesIO
import json
from urllib.parse import urlsplit

import flet as ft
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .scan_url import get_latest_report, run_phase1_scan


def _result_sections(data):
    target = data["target"]
    dns = data["dns"]
    discovery = data["subdomain_discovery"]

    subdomain_lines = [
        f"Candidates: {discovery['candidates']}  |  Attempted: {discovery['attempted']}  |  "
        f"Unresolved: {discovery['unresolved']}  |  Timeouts: {discovery['timeouts']}"
    ]
    for item in discovery["results"]:
        subdomain_lines.append(
            f"{item['hostname']} [{item['status']}]  "
            f"IPs: {', '.join(item['addresses']) or 'none'}"
        )
    if not discovery["results"]:
        subdomain_lines.append("No resolving subdomains found.")
    if discovery["wordlist_error"]:
        subdomain_lines.append(discovery["wordlist_error"])
    if discovery["stopped_on_timeout"]:
        subdomain_lines.append("Discovery stopped after a DNS timeout.")

    host_lines = [
        f"{host['hostname']} [{host['status']}]  IPs: "
        f"{', '.join(host['addresses']) or 'none'}"
        for host in data["hosts"]
    ] or ["No resolved hosts found."]

    port_lines = [
        f"{item['address']}  {item['port']}/{item['protocol']} {item['state']}  "
        f"{item['service']}"
        + (f"  |  {item['version']}" if item["version"] else "")
        for item in data["ports"]
    ] or ["No open TCP ports found."]

    return [
        ("TARGET PROFILE", [
            f"URL: {target['input']}",
            f"Scheme: {target['scheme']}  |  Host: {target['hostname']}  |  "
            f"Port: {target['port']}  |  Path: {target['path']}",
        ]),
        ("DNS INFORMATION", [
            f"Status: {dns['status']}  |  {dns['message']}",
            f"Addresses: {', '.join(dns['addresses']) or 'none'}",
        ]),
        ("SUBDOMAIN DISCOVERY", subdomain_lines),
        ("IP / HOST DISCOVERY", host_lines),
        ("PORT & SERVICE INVENTORY", port_lines),
    ]


def _report_text(data):
    lines = [
        "ThreatLens Phase 1 Report",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
    ]
    for title, section_lines in _result_sections(data):
        lines.append(title)
        lines.extend(section_lines)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _report_pdf(data):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="ThreatLens Phase 1 Report",
    )
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "ThreatLensBody",
        parent=styles["BodyText"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#17212b"),
        splitLongWords=True,
    )
    story = [Paragraph("ThreatLens Phase 1 Report", styles["Title"]), Spacer(1, 5 * mm)]
    story.append(Paragraph(escape(f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}"), body))
    story.append(Spacer(1, 4 * mm))
    for title, section_lines in _result_sections(data):
        story.append(Paragraph(escape(title), styles["Heading2"]))
        for line in section_lines:
            story.append(Paragraph(escape(line) or "&nbsp;", body))
        story.append(Spacer(1, 3 * mm))
    document.build(story)
    return buffer.getvalue()


def _report_html(data):
    sections = []
    for title, lines in _result_sections(data):
        items = "".join(f"<li>{escape(line)}</li>" for line in lines)
        sections.append(f"<section><h2>{escape(title)}</h2><ul>{items}</ul></section>")
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>ThreatLens Report</title>"
        "<style>body{font:14px Segoe UI,sans-serif;max-width:900px;margin:32px auto;padding:0 20px;color:#17212b}"
        "h1{color:#087f78}section{border-top:1px solid #cbd5df;padding:10px 0}li{margin:5px 0}</style></head><body>"
        f"<h1>ThreatLens Phase 1 Report</h1><p>Generated {escape(datetime.now().astimezone().isoformat(timespec='seconds'))}</p>"
        + "".join(sections)
        + "</body></html>"
    )


def _append_result_sections(results, data):
    for title, lines in _result_sections(data):
        results.controls.append(
            ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color="#00E5FF")
        )
        results.controls.append(
            ft.Text("\n".join(lines), size=13, color="#AFC5D6", selectable=True)
        )


def create_single_input_page():
    url_field = ft.TextField(
        label="Target URL",
        hint_text="https://example.com",
        width=520,
    )
    authorization = ft.Checkbox(
        label="I own this target or have permission to assess it",
        value=False,
    )
    wordlist_field = ft.TextField(
        label="Subdomain wordlist path (optional)",
        hint_text="One subdomain label per line",
        width=520,
    )
    max_candidates_field = ft.TextField(label="DNS candidate cap", value="500", width=160)
    dns_delay_field = ft.TextField(label="DNS delay (ms)", value="100", width=160)
    port_mode = ft.Dropdown(
        label="TCP ports",
        value="common",
        width=250,
        options=[
            ft.dropdown.Option("common", "Common ports"),
            ft.dropdown.Option("list", "Custom list"),
            ft.dropdown.Option("full", "Full TCP range"),
        ],
    )
    ports_field = ft.TextField(
        label="Ports, comma-separated",
        hint_text="22,80,443,8080",
        width=250,
        visible=False,
    )
    full_range_confirmation = ft.Checkbox(
        label="Confirm scan of TCP ports 1-65535",
        value=False,
        visible=False,
    )
    timeout_field = ft.TextField(label="TCP timeout (ms)", value="500", width=160)
    concurrency_field = ft.TextField(label="Workers (max 32)", value="8", width=160)
    status_text = ft.Text(size=13, color="#F6C177")
    progress = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2)
    results = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
    scan_button = ft.Button(content="Run Phase 1 Scan")
    latest_report = get_latest_report()
    if latest_report:
        url_field.value = latest_report["target"]["input"]
        _append_result_sections(results, latest_report)

    def on_port_mode_change(event):
        ports_field.visible = port_mode.value == "list"
        full_range_confirmation.visible = port_mode.value == "full"
        event.page.update()

    port_mode.on_change = on_port_mode_change

    async def on_scan(event):
        url = (url_field.value or "").strip()
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            status_text.value = "Enter a valid http:// or https:// URL."
            event.page.update()
            return
        if not authorization.value:
            status_text.value = "Confirm that you are authorized to scan this target."
            event.page.update()
            return
        if port_mode.value == "full" and not full_range_confirmation.value:
            status_text.value = "Confirm the full TCP range scan before starting."
            event.page.update()
            return
        if port_mode.value == "list" and not (ports_field.value or "").strip():
            status_text.value = "Enter at least one TCP port for custom-list mode."
            event.page.update()
            return

        try:
            max_candidates = int(max_candidates_field.value or "500")
            dns_delay_ms = int(dns_delay_field.value or "100")
            timeout_ms = int(timeout_field.value or "500")
            concurrency = int(concurrency_field.value or "8")
        except ValueError:
            status_text.value = "Candidate cap, delay, timeout, and worker count must be numbers."
            event.page.update()
            return

        status_text.value = "Scanning authorized target..."
        progress.visible = True
        scan_button.disabled = True
        results.controls.clear()
        event.page.update()

        try:
            data = await run_phase1_scan(
                url,
                authorized=bool(authorization.value),
                wordlist_path=wordlist_field.value or "",
                max_candidates=max_candidates,
                dns_delay_ms=dns_delay_ms,
                port_mode=port_mode.value or "common",
                ports=ports_field.value or "",
                timeout_ms=timeout_ms,
                concurrency=concurrency,
                full_range_confirmed=bool(full_range_confirmation.value),
            )
            status_text.value = "Scan complete."
            _append_result_sections(results, data)
        except Exception as error:
            status_text.value = str(error)
        finally:
            progress.visible = False
            scan_button.disabled = False
            event.page.update()

    scan_button.on_click = on_scan

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("SCAN", size=10, color="#20E3B2", weight=ft.FontWeight.BOLD),
                                ft.Text("Quick Phase 1 Recon", size=22, color="#E2E8F0", weight=ft.FontWeight.BOLD),
                                ft.Text("Execute native C++17 multi-worker DNS, host discovery, and port enumeration.", size=12, color="#8A9BA8"),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            url_field,
                            authorization,
                            wordlist_field,
                            ft.Row([max_candidates_field, dns_delay_field], wrap=True),
                            ft.Row([port_mode, ports_field, full_range_confirmation], wrap=True),
                            ft.Row([timeout_field, concurrency_field], wrap=True),
                            ft.Row([scan_button, progress, status_text], wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ],
                        spacing=12,
                    ),
                    padding=16,
                    bgcolor="#0E1726",
                    border=ft.Border.all(1, "#1E2F45"),
                    border_radius=8,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("SCAN TELEMETRY & RESULTS", size=11, color="#8A9BA8", weight=ft.FontWeight.BOLD),
                            results,
                        ],
                        spacing=10,
                        expand=True,
                    ),
                    padding=16,
                    bgcolor="#0E1726",
                    border=ft.Border.all(1, "#1E2F45"),
                    border_radius=8,
                    expand=True,
                ),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )


def create_reports_page():
    report = get_latest_report()
    status = ft.Text(size=13, color="#F6C177")
    content = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    if report is None:
        content.controls.append(ft.Text("No scan report yet. Run a Phase 1 scan first.", color="#AFC5D6"))
    else:
        for title, lines in _result_sections(report):
            content.controls.append(
                ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color="#00E5FF")
            )
            content.controls.append(
                ft.Text("\n".join(lines), size=13, color="#AFC5D6", selectable=True)
            )

    async def copy_report(event):
        current_report = get_latest_report()
        if current_report is None:
            status.value = "No report to copy."
        else:
            clipboard = ft.Clipboard()
            event.page.services.append(clipboard)
            await clipboard.set(_report_text(current_report))
            status.value = "Report copied to clipboard."
        event.page.update()

    async def save_report(event, extension):
        current_report = get_latest_report()
        if current_report is None:
            status.value = "No report to export."
            event.page.update()
            return

        picker = ft.FilePicker()
        event.page.services.append(picker)
        if extension == "pdf":
            file_bytes = _report_pdf(current_report)
            file_type = ft.FilePickerFileType.CUSTOM
            allowed_extensions = ["pdf"]
        elif extension == "json":
            file_bytes = json.dumps(current_report, indent=2, ensure_ascii=False).encode("utf-8")
            file_type = ft.FilePickerFileType.CUSTOM
            allowed_extensions = ["json"]
        elif extension == "html":
            file_bytes = _report_html(current_report).encode("utf-8")
            file_type = ft.FilePickerFileType.CUSTOM
            allowed_extensions = ["html"]
        else:
            file_bytes = _report_text(current_report).encode("utf-8")
            file_type = ft.FilePickerFileType.CUSTOM
            allowed_extensions = ["txt"]

        saved_path = await picker.save_file(
            dialog_title="Export ThreatLens report",
            file_name=f"ThreatLens-{current_report['target']['hostname']}.{extension}",
            file_type=file_type,
            allowed_extensions=allowed_extensions,
            src_bytes=file_bytes,
        )
        status.value = f"Report saved: {saved_path}" if saved_path else "Export cancelled."
        event.page.update()

    return ft.Container(
        expand=True,
        padding=24,
        content=ft.Column(
            [
                ft.Text("Latest Scan Report", size=24, color="#00E5FF", weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Button("Copy Report", on_click=copy_report),
                        ft.Button("Export JSON", on_click=lambda event: save_report(event, "json")),
                        ft.Button("Export TXT", on_click=lambda event: save_report(event, "txt")),
                        ft.Button("Export HTML", on_click=lambda event: save_report(event, "html")),
                        ft.Button("Export PDF", on_click=lambda event: save_report(event, "pdf")),
                    ],
                    wrap=True,
                ),
                status,
                ft.Divider(),
                content,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
    )