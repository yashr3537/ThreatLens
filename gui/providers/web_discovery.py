import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

from .http_client import http_probe, normalize_http_url
from .result import ToolResult


MAX_DIRECTORY_REQUESTS = 100
MIN_DIRECTORY_DELAY_MS = 250
MAX_WEB_ITEMS = 500


def _same_origin(first, second):
    left = urlsplit(first)
    right = urlsplit(second)
    left_port = left.port or (443 if left.scheme == "https" else 80)
    right_port = right.port or (443 if right.scheme == "https" else 80)
    return (left.scheme.lower(), left.hostname.lower() if left.hostname else "", left_port) == (
        right.scheme.lower(), right.hostname.lower() if right.hostname else "", right_port
    )


class _LinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.endpoints = []
        self.scripts = []

    def _add(self, raw_url, method="GET", source="HTML"):
        if not raw_url or raw_url.startswith(("#", "javascript:", "mailto:", "data:")):
            return
        resolved = urljoin(self.base_url, raw_url)
        if not _same_origin(self.base_url, resolved):
            return
        parsed = urlsplit(resolved)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return
        if len(self.endpoints) < MAX_WEB_ITEMS:
            self.endpoints.append({
                "url": resolved,
                "method": method.upper(),
                "type": "API" if "/api/" in parsed.path.lower() or "openapi" in parsed.path.lower() else "Web route",
                "parameters": sorted(parse_qs(parsed.query).keys()),
                "source": source,
                "status": "not_probed",
            })

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        tag = tag.lower()
        if tag == "a":
            self._add(attributes.get("href"), "GET", "anchor")
        elif tag == "form":
            self._add(attributes.get("action") or self.base_url, attributes.get("method", "GET"), "form")
        elif tag == "script" and attributes.get("src"):
            resolved = urljoin(self.base_url, attributes["src"])
            if _same_origin(self.base_url, resolved) and len(self.scripts) < MAX_WEB_ITEMS:
                self.scripts.append(resolved)


def discover_web_surface(target, http_result):
    if http_result.status != "completed":
        return ToolResult("endpoints", target, "failed", errors=list(http_result.errors))
    content_type = http_result.data.get("content_type", "")
    body = http_result.data.get("_body_for_analysis", "")
    if "html" not in content_type.lower() or not body:
        return ToolResult("endpoints", target, "completed", data={"urls": [], "endpoints": [], "javascript": []}, errors=["Response did not contain a readable HTML body."])

    base_url = http_result.data.get("final_url", target)
    parser = _LinkParser(base_url)
    try:
        parser.feed(body)
    except Exception as error:
        return ToolResult("endpoints", target, "failed", errors=[f"Could not parse HTML response: {error}"])

    unique = {}
    for endpoint in parser.endpoints:
        unique[(endpoint["method"], endpoint["url"])] = endpoint
    endpoints = list(unique.values())
    scripts = sorted(set(parser.scripts))
    return ToolResult(
        "endpoints",
        target,
        "completed",
        data={"urls": sorted({item["url"] for item in endpoints}), "endpoints": endpoints, "javascript": scripts},
        evidence=[{"kind": "html_reference", "url": item["url"], "source": item["source"]} for item in endpoints],
    )


def discover_directories(target, wordlist_path, max_requests=100, delay_ms=250):
    try:
        base_url = normalize_http_url(target)
    except ValueError as error:
        return ToolResult("directory", target or "", "failed", errors=[str(error)])
    try:
        request_limit = max(1, min(int(max_requests), MAX_DIRECTORY_REQUESTS))
        delay = max(MIN_DIRECTORY_DELAY_MS, min(int(delay_ms), 5000))
    except (TypeError, ValueError):
        return ToolResult("directory", base_url, "failed", errors=["Request limit and delay must be whole numbers."])
    if not wordlist_path:
        return ToolResult("directory", base_url, "failed", errors=["Select a local wordlist to run directory discovery."])

    path = Path(wordlist_path)
    try:
        words = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as error:
        return ToolResult("directory", base_url, "failed", errors=[f"Could not read wordlist: {error}"])

    results = []
    errors = []
    candidates = []
    for line in words:
        word = line.strip()
        if not word or word.startswith(("#", ";")):
            continue
        candidate_path = word.lstrip("/")
        if ".." in candidate_path.split("/") or "://" in candidate_path or "\\" in candidate_path:
            continue
        candidates.append(candidate_path)
        if len(candidates) >= request_limit:
            break

    for index, candidate in enumerate(candidates):
        candidate_url = urljoin(base_url.rstrip("/") + "/", candidate)
        if not _same_origin(base_url, candidate_url):
            continue
        result = http_probe(candidate_url, include_body=False)
        if result.status == "completed":
            code = result.data.get("status_code")
            if code not in (404, 410):
                results.append({
                    "url": result.data.get("final_url", candidate_url),
                    "status_code": code,
                    "content_type": result.data.get("content_type", ""),
                    "content_length": result.data.get("content_length"),
                    "response_time_ms": result.data.get("response_time_ms"),
                })
        else:
            errors.extend(result.errors)
        if index + 1 < len(candidates):
            time.sleep(delay / 1000.0)

    return ToolResult(
        "directory",
        base_url,
        "completed",
        data={"requested_candidates": len(candidates), "matches": results, "max_requests": request_limit, "delay_ms": delay},
        errors=list(dict.fromkeys(errors)),
        evidence=[{"kind": "http_path_response", **item} for item in results],
    )