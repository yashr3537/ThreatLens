import flet as ft


NAV_SECTIONS = [
    ("Workspace", [
        ("dashboard", "Dashboard", ft.Icons.DASHBOARD_OUTLINED),
    ]),
    ("Scan", [
        ("scan_center", "Scan Center", ft.Icons.RADAR),
        ("quick_scan", "Quick Scan", ft.Icons.PLAY_ARROW),
        ("custom_scan", "Custom Scan", ft.Icons.TUNE),
        ("live_scan", "Live Scan", ft.Icons.TRACK_CHANGES),
    ]),
    ("Targets", [
        ("targets", "Targets", ft.Icons.PUBLIC),
        ("assets", "Assets", ft.Icons.INVENTORY_2_OUTLINED),
        ("asset_graph", "Asset Graph", ft.Icons.HUB),
        ("target_explorer", "Target Explorer", ft.Icons.EXPLORE_OUTLINED),
    ]),
    ("Analysis", [
        ("findings", "Findings", ft.Icons.BUG_REPORT_OUTLINED),
        ("endpoints", "Endpoints", ft.Icons.ROUTE),
        ("technologies", "Technologies", ft.Icons.DEVELOPER_BOARD_OUTLINED),
        ("network", "Network", ft.Icons.LAN),
        ("web_intelligence", "Web Intelligence", ft.Icons.WEB),
    ]),
    ("Tools", [
        ("dns_lookup", "DNS Lookup", ft.Icons.DNS),
        ("port_scanner", "Port Scanner", ft.Icons.ROUTER_OUTLINED),
        ("http_inspector", "HTTP Inspector", ft.Icons.HTTP),
        ("tls_inspector", "TLS Inspector", ft.Icons.LOCK_OUTLINE),
        ("header_analyzer", "Header Analyzer", ft.Icons.TEXT_SNIPPET),
        ("cookie_analyzer", "Cookie Analyzer", ft.Icons.COOKIE_OUTLINED),
        ("technology_detector", "Technology Detector", ft.Icons.FINGERPRINT),
        ("url_analyzer", "URL Analyzer", ft.Icons.LINK),
    ]),
    ("Output", [
        ("reports", "Reports", ft.Icons.ARTICLE_OUTLINED),
        ("evidence", "Evidence", ft.Icons.FOLDER_OUTLINED),
        ("scan_history", "Scan History", ft.Icons.HISTORY),
    ]),
    ("System", [
        ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED),
    ]),
]


PAGE_LABELS = {
    page_id: label
    for _, items in NAV_SECTIONS
    for page_id, label, _ in items
}