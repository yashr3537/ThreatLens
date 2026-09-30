import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, status_badge
from .scan_url import get_latest_report


def create_asset_graph_page(page, open_page):
    report = get_latest_report()
    nodes = []
    if report:
        target = report.get("target", {}).get("hostname", "")
        if target:
            nodes.append({"name": target, "type": "Target", "detail": "Scanned target", "tone": COLORS["accent"]})
        for item in report.get("subdomain_discovery", {}).get("results", []):
            nodes.append({"name": item.get("hostname", ""), "type": "Subdomain", "detail": ", ".join(item.get("addresses", [])), "tone": COLORS["blue"]})
        for host in report.get("hosts", []):
            for address in host.get("addresses", []):
                nodes.append({"name": address, "type": "IP", "detail": host.get("hostname", ""), "tone": COLORS["lime"]})
        for port in report.get("ports", []):
            nodes.append({"name": f"{port.get('port')}/{port.get('protocol')}", "type": "Port", "detail": port.get("service", ""), "tone": COLORS["amber"]})
    nodes = list({(node["type"], node["name"]): node for node in nodes}.values())

    search = ft.TextField(hint_text="Search discovered nodes...", width=250, dense=True)
    node_type = ft.Dropdown(label="Node type", value="All", width=150, dense=True, options=[ft.dropdown.Option(value) for value in ["All", "Target", "Subdomain", "IP", "Port"]])
    zoom_value = ft.Text("100%", size=10, color=COLORS["muted"])
    selected = {"node": None}
    inspector = ft.Container(expand=True)
    graph = ft.Container(expand=True)

    def update_inspector(node):
        selected["node"] = node
        inspector.content = panel(
            [
                ft.Text(node["name"], size=14, color=COLORS["text"], weight=ft.FontWeight.BOLD, selectable=True),
                status_badge(node["type"], node["tone"]),
                ft.Text(node["detail"] or "No additional scanner detail.", size=11, color=COLORS["muted"], selectable=True),
                ft.Row([ft.Button("Scan target", icon=ft.Icons.RADAR, on_click=lambda event: open_page("scan_center")), ft.OutlinedButton("Target explorer", on_click=lambda event: open_page("target_explorer"))], wrap=True),
            ],
            title="Selected node",
        )

    def render(event=None):
        query = (search.value or "").strip().lower()
        selected_type = node_type.value or "All"
        filtered = [node for node in nodes if (not query or query in f"{node['name']} {node['detail']}".lower()) and (selected_type == "All" or node["type"] == selected_type)]
        if not filtered:
            graph.content = empty_state(ft.Icons.HUB, "No graph data available", "Complete a real Phase 1 scan to show target, subdomain, IP, and port nodes.")
            inspector.content = empty_state(ft.Icons.INFO_OUTLINED, "No node selected", "Node details appear here after scan data is available.")
        else:
            graph.content = ft.ResponsiveRow(
                [
                    ft.Container(
                        content=ft.Column([status_badge(node["type"], node["tone"]), ft.Text(node["name"], size=11, color=COLORS["text"], selectable=True), ft.Text(node["detail"], size=9, color=COLORS["muted"], max_lines=2)], spacing=5),
                        padding=12,
                        bgcolor=COLORS["panel"],
                        border=ft.Border.all(1, COLORS["line"]),
                        border_radius=6,
                        on_click=lambda click, item=node: update_inspector(item),
                        tooltip="Inspect this real scanner node",
                        col={"xs": 12, "sm": 6, "lg": 3},
                    )
                    for node in filtered
                ],
                spacing=8,
                run_spacing=8,
            )
            if selected["node"] not in filtered:
                update_inspector(filtered[0])
        if event:
            event.page.update()

    search.on_change = render
    node_type.on_change = render
    render()

    def change_zoom(amount):
        current = int(zoom_value.value.rstrip("%"))
        zoom_value.value = f"{max(50, min(150, current + amount))}%"

    return ft.Container(
        expand=True,
        padding=ft.Padding.only(left=22, top=18, right=22, bottom=18),
        content=ft.Column(
            [
                page_heading("Targets", "Asset topology", "Relationships generated only from completed scanner results."),
                ft.Row([search, node_type, ft.Container(expand=True), ft.IconButton(ft.Icons.ZOOM_OUT, tooltip="Zoom out", on_click=lambda event: change_zoom(-10)), zoom_value, ft.IconButton(ft.Icons.ZOOM_IN, tooltip="Zoom in", on_click=lambda event: change_zoom(10)), ft.IconButton(ft.Icons.REPLAY, tooltip="Reset view", on_click=lambda event: (setattr(zoom_value, "value", "100%"), render(event))), ft.IconButton(ft.Icons.FULLSCREEN, tooltip="Fullscreen", on_click=lambda event: None)], wrap=True),
                panel([graph], title="Discovered nodes", expand=True),
                inspector,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )