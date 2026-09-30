import flet as ft

from ..components import COLORS, empty_state, page_heading, panel, show_notice, show_toast, status_badge, tag_chip
from ..workspace_data import (
    add_target,
    delete_target,
    get_all_targets,
    update_target_notes,
    update_target_tags,
)


def create_targets_page(page, open_page):
    search_box = ft.TextField(
        hint_text="Search targets or tags...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=260,
        dense=True,
    )
    type_filter = ft.Dropdown(
        label="Target Type",
        value="All",
        width=150,
        dense=True,
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(opt) for opt in ["External", "Cloud / API", "Staging", "Internal", "URL / domain"]],
    )
    status_filter = ft.Dropdown(
        label="Status",
        value="All",
        width=140,
        dense=True,
        options=[ft.dropdown.Option("All"), ft.dropdown.Option("Active"), ft.dropdown.Option("Completed")],
    )

    table_container = ft.Container(expand=True)
    count_text = ft.Text(size=11, color=COLORS["muted"])

    def open_add_target_dialog(e=None):
        target_name_field = ft.TextField(label="Target URL or Hostname", hint_text="e.g. portal.domain.com", autofocus=True)
        target_type_dd = ft.Dropdown(
            label="Environment / Type",
            value="External",
            options=[ft.dropdown.Option(opt) for opt in ["External", "Cloud / API", "Staging", "Internal"]],
        )
        tag_prod = ft.Checkbox(label="Production", value=True, active_color=COLORS["accent"])
        tag_imp = ft.Checkbox(label="Important", value=False, active_color=COLORS["accent"])
        tag_api = ft.Checkbox(label="API", value=False, active_color=COLORS["accent"])
        tag_rev = ft.Checkbox(label="Review", value=True, active_color=COLORS["accent"])
        notes_field = ft.TextField(label="Target Notes", multiline=True, min_lines=2, hint_text="Scope notes or compliance details...")

        def on_submit(ev):
            name = (target_name_field.value or "").strip()
            if not name:
                show_toast(page, "Please enter a target name.", COLORS["red"])
                return

            chosen_tags = []
            if tag_prod.value: chosen_tags.append("Production")
            if tag_imp.value: chosen_tags.append("Important")
            if tag_api.value: chosen_tags.append("API")
            if tag_rev.value: chosen_tags.append("Review")

            add_target(name, target_type_dd.value, chosen_tags, notes_field.value)
            page.pop_dialog()
            render_table()
            show_toast(page, f"Target '{name}' added successfully.", COLORS["lime"])

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row([ft.Icon(ft.Icons.ADD_LOCATION_ALT, color=COLORS["accent"]), ft.Text("Enroll New Target", size=15, weight=ft.FontWeight.BOLD)]),
                content=ft.Container(
                    content=ft.Column(
                        [
                            target_name_field,
                            target_type_dd,
                            ft.Text("INITIAL TAGS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD),
                            ft.Row([tag_prod, tag_imp, tag_api, tag_rev], wrap=True),
                            notes_field,
                        ],
                        spacing=10,
                        tight=True,
                    ),
                    width=480,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: page.pop_dialog()),
                    ft.Button("Add Target", on_click=on_submit),
                ],
            )
        )

    def open_notes_dialog(target_obj):
        notes_edit = ft.TextField(value=target_obj.get("notes", ""), multiline=True, min_lines=4, expand=True)

        def save_notes_click(ev):
            update_target_notes(target_obj["id"], notes_edit.value)
            target_obj["notes"] = notes_edit.value
            page.pop_dialog()
            render_table()
            show_toast(page, "Target notes saved.", COLORS["lime"])

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row([ft.Icon(ft.Icons.NOTE_ALT_OUTLINED, color=COLORS["accent"]), ft.Text(f"Notes: {target_obj['target']}", size=14, weight=ft.FontWeight.BOLD)]),
                content=ft.Container(content=notes_edit, width=460, height=180),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: page.pop_dialog()),
                    ft.Button("Save Notes", on_click=save_notes_click),
                ],
            )
        )

    def open_tags_dialog(target_obj):
        tags_list = list(target_obj.get("tags", []))
        new_tag_field = ft.TextField(hint_text="Add tag (e.g. PCI-DSS, Critical)", width=240, dense=True)
        chips_row = ft.Row(wrap=True, spacing=6)

        def refresh_chips():
            chips_row.controls.clear()
            for t in tags_list:
                chips_row.controls.append(
                    tag_chip(t, on_delete=lambda e, tg=t: remove_tag_click(tg))
                )
            page.update()

        def remove_tag_click(tag_to_remove):
            if tag_to_remove in tags_list:
                tags_list.remove(tag_to_remove)
                update_target_tags(target_obj["id"], tags_list)
                refresh_chips()

        def add_tag_click(e):
            val = (new_tag_field.value or "").strip()
            if val and val not in tags_list:
                tags_list.append(val)
                update_target_tags(target_obj["id"], tags_list)
                new_tag_field.value = ""
                refresh_chips()

        refresh_chips()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row([ft.Icon(ft.Icons.LABEL, color=COLORS["accent"]), ft.Text(f"Manage Tags: {target_obj['target']}", size=14, weight=ft.FontWeight.BOLD)]),
                content=ft.Container(
                    content=ft.Column(
                        [
                            chips_row,
                            ft.Divider(color=COLORS["line"]),
                            ft.Row([new_tag_field, ft.Button("Add", on_click=add_tag_click)], spacing=8),
                        ],
                        tight=True,
                        spacing=12,
                    ),
                    width=440,
                ),
                actions=[
                    ft.Button("Done", on_click=lambda e: (page.pop_dialog(), render_table())),
                ],
            )
        )

    def handle_row_action(action, target_obj):
        if action == "Open":
            open_page("target_explorer")
        elif action in ("Scan", "Rescan"):
            open_page("scan_center")
        elif action == "Notes":
            open_notes_dialog(target_obj)
        elif action == "Tags":
            open_tags_dialog(target_obj)
        elif action == "Rename":
            rename_field = ft.TextField(value=target_obj["target"])
            def on_rename(e):
                val = (rename_field.value or "").strip()
                if val:
                    target_obj["target"] = val
                    page.pop_dialog()
                    render_table()
                    show_toast(page, "Target renamed.", COLORS["lime"])
            page.show_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Rename Target"),
                    content=rename_field,
                    actions=[ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()), ft.Button("Save", on_click=on_rename)],
                )
            )
        elif action == "Delete":
            delete_target(target_obj["id"])
            render_table()
            show_toast(page, f"Target '{target_obj['target']}' removed.", COLORS["amber"])
        elif action == "Export":
            open_page("reports")

    def render_table(event=None):
        q = (search_box.value or "").strip().lower()
        t_filter = type_filter.value
        s_filter = status_filter.value

        all_targets = get_all_targets()
        filtered = [
            t for t in all_targets
            if (not q or q in t["target"].lower() or any(q in tag.lower() for tag in t.get("tags", [])))
            and (t_filter == "All" or t.get("type", "").lower() == t_filter.lower())
            and (s_filter == "All" or t.get("status", "").lower() == s_filter.lower())
        ]

        count_text.value = f"{len(filtered)} targets active"

        if not filtered:
            table_container.content = empty_state(
                ft.Icons.PUBLIC_OFF,
                "No targets found",
                "Try adjusting your search criteria or add a new target.",
                action=ft.Button("Add Target", icon=ft.Icons.ADD, on_click=open_add_target_dialog),
            )
        else:
            rows = []
            for t in filtered:
                tag_controls = [tag_chip(tag) for tag in t.get("tags", [])[:2]]
                if len(t.get("tags", [])) > 2:
                    tag_controls.append(status_badge(f"+{len(t['tags']) - 2}", COLORS["muted"]))

                tags_cell = ft.Row(tag_controls, spacing=4, wrap=False)
                finding_count = t.get("findings")
                findings_cell = (
                    status_badge("N/A", COLORS["muted"])
                    if finding_count is None
                    else status_badge(
                        f"{finding_count} Findings",
                        COLORS["red"] if finding_count > 3 else (COLORS["amber"] if finding_count > 0 else COLORS["lime"]),
                    )
                )

                action_menu = ft.PopupMenuButton(
                    icon=ft.Icons.MORE_HORIZ,
                    items=[
                        ft.PopupMenuItem(content="Open Explorer", on_click=lambda e, tobj=t: handle_row_action("Open", tobj)),
                        ft.PopupMenuItem(content="Launch Scan", on_click=lambda e, tobj=t: handle_row_action("Scan", tobj)),
                        ft.PopupMenuItem(content="Manage Tags", on_click=lambda e, tobj=t: handle_row_action("Tags", tobj)),
                        ft.PopupMenuItem(content="Edit Notes", on_click=lambda e, tobj=t: handle_row_action("Notes", tobj)),
                        ft.PopupMenuItem(content="Rename", on_click=lambda e, tobj=t: handle_row_action("Rename", tobj)),
                        ft.PopupMenuItem(content="Export Report", on_click=lambda e, tobj=t: handle_row_action("Export", tobj)),
                        ft.PopupMenuItem(content="Delete Target", on_click=lambda e, tobj=t: handle_row_action("Delete", tobj)),
                    ],
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.LANGUAGE, size=15, color=COLORS["accent"]),
                                        ft.Text(t["target"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD, selectable=True),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                            ),
                            ft.DataCell(ft.Text(t.get("type", "External"), size=11, color=COLORS["muted"])),
                            ft.DataCell(status_badge(t.get("status", "Active"), COLORS["lime"] if t.get("status") == "Active" else COLORS["blue"])),
                            ft.DataCell(ft.Text(str(t.get("assets") if t.get("assets") is not None else "N/A"), size=11, color=COLORS["text"], weight=ft.FontWeight.W_500)),
                            ft.DataCell(findings_cell),
                            ft.DataCell(tags_cell),
                            ft.DataCell(ft.Text(t.get("last_scan", "Never"), size=10, color=COLORS["muted"])),
                            ft.DataCell(action_menu),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("TARGET", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("TYPE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("STATUS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ASSETS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("FINDINGS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("TAGS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("LAST SCAN", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ACTIONS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                column_spacing=18,
                horizontal_margin=12,
                heading_row_height=40,
                data_row_min_height=44,
                heading_row_color=COLORS["raised"],
                bgcolor=COLORS["panel"],
                border_radius=8,
            )
            table_container.content = ft.Row([data_table], scroll=ft.ScrollMode.AUTO)

        if event:
            page.update()

    search_box.on_change = render_table
    type_filter.on_change = render_table
    status_filter.on_change = render_table
    render_table()

    toolbar = ft.Row(
        [
            ft.Button("Add Target", icon=ft.Icons.ADD, on_click=open_add_target_dialog),
            search_box,
            type_filter,
            status_filter,
            ft.Container(expand=True),
            count_text,
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh Targets", on_click=render_table),
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
                    "Targets",
                    "Target Management & Inventory",
                    "Manage root domains, IP subnets, and web applications within your assessment scope.",
                ),
                panel([toolbar, table_container], title="Enrolled Targets", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )


def create_assets_page(page, open_page):
    from .scan_url import get_report_history

    search_input = ft.TextField(
        hint_text="Search assets by hostname, IP address...",
        prefix=ft.Icon(ft.Icons.SEARCH, size=16, color=COLORS["muted"]),
        width=280,
        dense=True,
    )
    res_filter = ft.Dropdown(
        label="Resolution",
        value="All",
        width=140,
        dense=True,
        options=[ft.dropdown.Option("All"), ft.dropdown.Option("Resolved"), ft.dropdown.Option("Unresolved")],
    )

    table_container = ft.Container(expand=True)
    count_text = ft.Text(size=11, color=COLORS["muted"])

    default_asset_rows = []
    unique_assets = set()
    for report in get_report_history():
        for host in report.get("hosts", []):
            for address in host.get("addresses", []):
                key = (host.get("hostname", "").lower(), address.lower())
                if key in unique_assets:
                    continue
                unique_assets.add(key)
                default_asset_rows.append({
                    "host": host.get("hostname", ""),
                    "address": address,
                    "resolution": host.get("status", "resolved").capitalize(),
                    "provider": "Not enriched by Phase 1",
                    "source": "Scanner DNS inventory",
                })

    def render_assets(e=None):
        q = (search_input.value or "").strip().lower()
        rf = res_filter.value

        filtered = [
            a for a in default_asset_rows
            if (not q or q in a["host"].lower() or q in a["address"].lower() or q in a["provider"].lower())
            and (rf == "All" or a["resolution"].lower() == rf.lower())
        ]
        count_text.value = f"{len(filtered)} discovered assets"

        if not filtered:
            table_container.content = empty_state(ft.Icons.INVENTORY_2_OUTLINED, "No assets found", "Try adjusting your search criteria.")
        else:
            rows = []
            for a in filtered:
                is_res = a["resolution"] == "Resolved"
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.COMPUTER if is_res else ft.Icons.ERROR_OUTLINE, size=15, color=COLORS["lime"] if is_res else COLORS["amber"]),
                                        ft.Text(a["host"], size=12, color=COLORS["text"], weight=ft.FontWeight.BOLD, selectable=True),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                            ),
                            ft.DataCell(ft.Text(a["address"], size=11, font_family="Consolas, Courier", color=COLORS["accent"], selectable=True)),
                            ft.DataCell(status_badge(a["resolution"], COLORS["lime"] if is_res else COLORS["amber"])),
                            ft.DataCell(ft.Text(a["provider"], size=11, color=COLORS["muted"])),
                            ft.DataCell(ft.Text(a["source"], size=11, color=COLORS["muted"])),
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Button("Scan", on_click=lambda ev, tg=a["host"]: open_page("scan_center")),
                                        ft.OutlinedButton("Explorer", on_click=lambda ev: open_page("target_explorer")),
                                    ],
                                    spacing=4,
                                )
                            ),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("HOSTNAME", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("IP ADDRESS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("STATUS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("INFRASTRUCTURE / ASN", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("DISCOVERY SOURCE", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ACTIONS", size=10, color=COLORS["muted"], weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                column_spacing=18,
                horizontal_margin=12,
                heading_row_height=40,
                data_row_min_height=44,
                heading_row_color=COLORS["raised"],
                bgcolor=COLORS["panel"],
                border_radius=8,
            )
            table_container.content = ft.Row([data_table], scroll=ft.ScrollMode.AUTO)

        if e:
            page.update()

    search_input.on_change = render_assets
    res_filter.on_change = render_assets
    render_assets()

    toolbar = ft.Row(
        [
            search_input,
            res_filter,
            ft.Container(expand=True),
            count_text,
            ft.Button("Asset Graph", icon=ft.Icons.HUB, on_click=lambda e: open_page("asset_graph")),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh Assets", on_click=render_assets),
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
                    "Targets",
                    "Discovered Assets & IP Infrastructure",
                    "Inventory of live IP addresses, resolved hostnames, reverse DNS records, and asset metadata across all targets.",
                ),
                panel([toolbar, table_container], title="Asset Inventory", expand=True),
            ],
            spacing=14,
            expand=True,
        ),
    )
