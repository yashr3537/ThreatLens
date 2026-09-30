import socket
import ssl
from urllib.parse import urlsplit

from .result import ToolResult


def inspect_tls(target, timeout_seconds=5):
    value = (target or "").strip()
    if not value:
        return ToolResult("tls", value, "failed", errors=["Target host is required."])
    if "://" not in value:
        value = "https://" + value
    parsed = urlsplit(value)
    if not parsed.hostname:
        return ToolResult("tls", target, "failed", errors=["Target must contain a valid hostname."])
    if parsed.scheme.lower() not in ("https", "http"):
        return ToolResult("tls", target, "failed", errors=["Only HTTPS/TLS targets are supported."])
    port = parsed.port or 443
    timeout = max(1.0, min(float(timeout_seconds), 8.0))
    context = ssl.create_default_context()

    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout) as raw_socket:
            with context.wrap_socket(raw_socket, server_hostname=parsed.hostname) as secure_socket:
                certificate = secure_socket.getpeercert()
                cipher = secure_socket.cipher()
                subject = {
                    key: value
                    for group in certificate.get("subject", [])
                    for key, value in group
                }
                issuer = {
                    key: value
                    for group in certificate.get("issuer", [])
                    for key, value in group
                }
                data = {
                    "hostname": parsed.hostname,
                    "port": port,
                    "subject": subject,
                    "issuer": issuer,
                    "not_before": certificate.get("notBefore"),
                    "not_after": certificate.get("notAfter"),
                    "subject_alt_names": [value for kind, value in certificate.get("subjectAltName", []) if kind == "DNS"],
                    "tls_version": secure_socket.version(),
                    "cipher": cipher[0] if cipher else None,
                    "cipher_protocol": cipher[1] if cipher else None,
                    "certificate_verified": True,
                    "chain_details": "Unavailable through the current Python TLS provider.",
                }
                return ToolResult("tls", target, "completed", data=data, evidence=[{"kind": "tls_certificate", **data}])
    except (OSError, ssl.SSLError, ValueError) as error:
        return ToolResult("tls", target, "failed", errors=[str(error)])