from http.cookies import SimpleCookie

from .result import ToolResult


SECURITY_HEADERS = (
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
)


def analyze_headers(target, http_result):
    if http_result.status != "completed":
        return ToolResult("headers", target, "failed", errors=list(http_result.errors))
    headers = http_result.data.get("headers", {})
    lookup = {key.lower(): value for key, value in headers.items()}
    observations = [
        {"name": name, "status": "present" if name.lower() in lookup else "missing", "value": lookup.get(name.lower())}
        for name in SECURITY_HEADERS
    ]
    return ToolResult(
        "headers",
        target,
        "completed",
        data={"status_code": http_result.data.get("status_code"), "headers": observations},
        evidence=[{"kind": "http_header", **item} for item in observations if item["status"] == "present"],
    )


def inspect_cookies(target, http_result):
    if http_result.status != "completed":
        return ToolResult("cookies", target, "failed", errors=list(http_result.errors))

    headers = http_result.data.get("headers", {})
    set_cookie_values = http_result.data.get("set_cookie_headers", [])
    if not set_cookie_values:
        set_cookie_values = [value for key, value in headers.items() if key.lower() == "set-cookie"]

    cookies = []
    errors = []
    for header in set_cookie_values:
        parsed = SimpleCookie()
        try:
            parsed.load(header)
        except Exception as error:
            errors.append(f"Could not parse Set-Cookie header: {error}")
            continue
        for name, morsel in parsed.items():
            cookies.append({
                "name": name,
                "secure": bool(morsel["secure"]),
                "http_only": bool(morsel["httponly"]),
                "same_site": morsel["samesite"] or None,
                "domain": morsel["domain"] or None,
                "path": morsel["path"] or None,
                "expires": morsel["expires"] or None,
            })
    return ToolResult(
        "cookies",
        target,
        "completed",
        data={"cookies": cookies},
        errors=errors,
        evidence=[{"kind": "set_cookie_attributes", **cookie} for cookie in cookies],
    )


def detect_technologies(target, http_result):
    if http_result.status != "completed":
        return ToolResult("technology", target, "failed", errors=list(http_result.errors))
    headers = http_result.data.get("headers", {})
    lowered = {key.lower(): value for key, value in headers.items()}
    detections = []

    def add(name, category, evidence):
        detections.append({"name": name, "category": category, "evidence": evidence})

    for header, category in (("server", "Server"), ("x-powered-by", "Framework"), ("via", "Proxy / CDN")):
        if lowered.get(header):
            add(lowered[header], category, f"HTTP response header: {header}")
    if "cf-ray" in lowered or lowered.get("server", "").lower() == "cloudflare":
        add("Cloudflare", "CDN", "HTTP response includes Cloudflare edge headers")
    if "x-amz-cf-id" in lowered or "x-amz-cf-pop" in lowered:
        add("Amazon CloudFront", "CDN", "HTTP response includes CloudFront headers")

    body = http_result.data.get("body_preview", "").lower()
    signatures = (
        ("wp-content", "WordPress", "CMS"),
        ("__next_data__", "Next.js", "Framework"),
        ("__nuxt__", "Nuxt", "Framework"),
        ("data-reactroot", "React", "JavaScript"),
        ("ng-version", "Angular", "JavaScript"),
    )
    for marker, name, category in signatures:
        if marker in body:
            add(name, category, f"Response body contains {marker}")

    return ToolResult(
        "technology",
        target,
        "completed",
        data={"detections": detections},
        evidence=[{"kind": "technology_signature", **item} for item in detections],
    )