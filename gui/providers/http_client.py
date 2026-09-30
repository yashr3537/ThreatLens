from html.parser import HTMLParser
from time import monotonic
from urllib.parse import urljoin, urlsplit

import requests

from .result import ToolResult


CONNECT_TIMEOUT_SECONDS = 3
READ_TIMEOUT_SECONDS = 5
MAX_RESPONSE_BYTES = 512 * 1024
MAX_REDIRECTS = 5


def normalize_http_url(target):
    value = (target or "").strip()
    if not value:
        raise ValueError("Target URL is required.")
    if "://" not in value:
        value = "https://" + value
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only valid HTTP and HTTPS URLs are supported.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in URLs are not supported.")
    return parsed.geturl()


def _origin(url):
    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), port


class _TitleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.parts.append(data.strip())


def extract_title(body, content_type):
    if "html" not in content_type.lower() or not body:
        return None
    parser = _TitleParser()
    try:
        parser.feed(body[:MAX_RESPONSE_BYTES].decode("utf-8", errors="replace"))
    except Exception:
        return None
    title = " ".join(part for part in parser.parts if part)
    return title[:512] or None


def http_probe(target, include_body=False):
    try:
        initial_url = normalize_http_url(target)
    except ValueError as error:
        return ToolResult("http_probe", target or "", "failed", errors=[str(error)])

    started = monotonic()
    redirects = []
    current_url = initial_url
    response = None
    errors = []
    session = requests.Session()
    session.trust_env = False
    session.headers.update({"User-Agent": "ThreatLens/1.0", "Accept": "*/*"})

    try:
        for _ in range(MAX_REDIRECTS + 1):
            response = session.get(
                current_url,
                allow_redirects=False,
                stream=True,
                timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
            )
            location = response.headers.get("Location")
            if response.status_code not in (301, 302, 303, 307, 308) or not location:
                break

            next_url = urljoin(current_url, location)
            redirects.append({"status": response.status_code, "from": current_url, "to": next_url})
            if _origin(next_url) != _origin(initial_url):
                errors.append("Redirect leaves the supplied origin; it was not followed.")
                break
            response.close()
            response = None
            current_url = next_url
        else:
            errors.append(f"Redirect limit ({MAX_REDIRECTS}) reached.")

        if response is None:
            raise requests.TooManyRedirects("Redirect limit reached before a final response.")

        body = bytearray()
        if include_body:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                remaining = MAX_RESPONSE_BYTES - len(body)
                if remaining <= 0:
                    errors.append("Response body was truncated at the configured size limit.")
                    break
                body.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    errors.append("Response body was truncated at the configured size limit.")
                    break

        content_type = response.headers.get("Content-Type", "")
        response_headers = {key: value for key, value in response.headers.items()}
        try:
            set_cookie_headers = response.raw.headers.getlist("Set-Cookie")
        except AttributeError:
            set_cookie_headers = [value for key, value in response.headers.items() if key.lower() == "set-cookie"]
        data = {
            "requested_url": initial_url,
            "final_url": current_url,
            "status_code": response.status_code,
            "headers": response_headers,
            "content_type": content_type,
            "content_length": response.headers.get("Content-Length"),
            "redirects": redirects,
            "response_time_ms": round((monotonic() - started) * 1000, 2),
            "title": extract_title(bytes(body), content_type) if include_body else None,
            "set_cookie_headers": set_cookie_headers,
        }
        if include_body:
            data["body_preview"] = bytes(body[:4096]).decode("utf-8", errors="replace")
            data["_body_for_analysis"] = bytes(body).decode("utf-8", errors="replace")
        result = ToolResult("http_probe", initial_url, "completed", data=data, errors=errors)
        result.evidence.append({"kind": "http_response", "status_code": response.status_code, "url": current_url})
        return result
    except requests.RequestException as error:
        return ToolResult(
            "http_probe",
            initial_url,
            "failed",
            data={"requested_url": initial_url, "redirects": redirects},
            errors=[str(error)],
        )
    finally:
        if response is not None:
            response.close()
        session.close()