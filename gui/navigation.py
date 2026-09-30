import flet as ft

from .components import COLORS
from .nav_items import PAGE_LABELS
from .pages.asset_graph import create_asset_graph_page
from .pages.custom_scan import create_custom_scan_page
from .pages.dashboard import create_dashboard
from .pages.endpoints import create_endpoints_page
from .pages.evidence import create_evidence_page
from .pages.findings import create_findings_page
from .pages.live_scan import create_live_scan_page
from .pages.network import create_network_page
from .pages.reports import create_reports_page
from .pages.scan_center import create_scan_center_page
from .pages.scan_history import create_scan_history_page
from .pages.settings import create_settings_page
from .pages.single_input import create_single_input_page
from .pages.target_explorer import create_target_explorer_page
from .pages.targets import create_assets_page, create_targets_page
from .pages.technologies import create_technologies_page
from .pages.tools import create_tool_page
from .pages.web_intel import create_web_intel_page


def create_center(page):
    center = ft.Container(
        expand=True,
        bgcolor=COLORS["canvas"],
    )

    active_page = {"value": "dashboard"}
    sidebar_ref = {"value": None}

    def navigate(page_id):
        if page_id not in PAGE_LABELS:
            page_id = "dashboard"

        active_page["value"] = page_id
        if sidebar_ref["value"] is not None:
            sidebar_ref["value"].set_active(page_id)

        if page_id == "dashboard":
            center.content = create_dashboard(navigate)
        elif page_id == "scan_center":
            center.content = create_scan_center_page(page, navigate)
        elif page_id == "quick_scan":
            center.content = create_single_input_page()
        elif page_id == "custom_scan":
            center.content = create_custom_scan_page(page, navigate)
        elif page_id == "live_scan":
            center.content = create_live_scan_page(page, navigate)
        elif page_id == "targets":
            center.content = create_targets_page(page, navigate)
        elif page_id == "assets":
            center.content = create_assets_page(page, navigate)
        elif page_id == "asset_graph":
            center.content = create_asset_graph_page(page, navigate)
        elif page_id == "target_explorer":
            center.content = create_target_explorer_page(page, navigate)
        elif page_id == "findings":
            center.content = create_findings_page(page, navigate)
        elif page_id == "endpoints":
            center.content = create_endpoints_page(page, navigate)
        elif page_id == "technologies":
            center.content = create_technologies_page(page, navigate)
        elif page_id == "network":
            center.content = create_network_page(page, navigate)
        elif page_id == "web_intelligence":
            center.content = create_web_intel_page(page, navigate)
        elif page_id in (
            "dns_lookup",
            "port_scanner",
            "http_inspector",
            "tls_inspector",
            "header_analyzer",
            "cookie_analyzer",
            "technology_detector",
            "url_analyzer",
        ):
            center.content = create_tool_page(page, page_id, navigate)
        elif page_id == "reports":
            center.content = create_reports_page(page, navigate)
        elif page_id == "evidence":
            center.content = create_evidence_page(page, navigate)
        elif page_id == "scan_history":
            center.content = create_scan_history_page(page, navigate)
        elif page_id == "settings":
            center.content = create_settings_page(page, navigate)
        else:
            center.content = create_dashboard(navigate)

        center.update()

    center.navigate = navigate
    center.set_sidebar = lambda sidebar: sidebar_ref.update(value=sidebar)
    center.active_page = active_page
    center.content = create_dashboard(navigate)

    return center