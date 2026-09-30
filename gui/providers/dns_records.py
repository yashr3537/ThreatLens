import dns.exception
import dns.resolver

from .result import ToolResult


SUPPORTED_RECORD_TYPES = ("A", "AAAA", "CNAME", "MX", "NS", "TXT")


def lookup_dns_records(target, record_types=SUPPORTED_RECORD_TYPES, timeout_seconds=3):
    name = (target or "").strip().rstrip(".")
    if not name:
        return ToolResult("dns_records", target or "", "failed", errors=["Domain is required."])

    selected = tuple(dict.fromkeys(record.upper() for record in record_types))
    unsupported = sorted(set(selected) - set(SUPPORTED_RECORD_TYPES))
    if unsupported:
        return ToolResult("dns_records", name, "failed", errors=["Unsupported record type(s): " + ", ".join(unsupported)])

    resolver = dns.resolver.Resolver(configure=True)
    resolver.timeout = max(0.5, min(float(timeout_seconds), 5.0))
    resolver.lifetime = max(0.5, min(float(timeout_seconds), 5.0))
    records = []
    errors = []

    for record_type in selected:
        try:
            answer = resolver.resolve(name, record_type, lifetime=resolver.lifetime, raise_on_no_answer=False)
            if answer.rrset is None:
                continue
            ttl = answer.rrset.ttl
            for value in answer:
                records.append({
                    "name": name,
                    "type": record_type,
                    "ttl": ttl,
                    "value": value.to_text(),
                })
        except dns.resolver.NXDOMAIN:
            errors.append(f"{record_type}: domain does not exist")
        except dns.exception.Timeout:
            errors.append(f"{record_type}: DNS query timed out")
        except dns.resolver.NoNameservers:
            errors.append(f"{record_type}: no DNS nameserver responded")
        except dns.exception.DNSException as error:
            errors.append(f"{record_type}: {error}")

    status = "completed" if records else "failed" if errors else "completed"
    return ToolResult(
        tool="dns_records",
        target=name,
        status=status,
        data={"records": records, "requested_types": list(selected)},
        errors=errors,
        evidence=[{"kind": "dns_record", **record} for record in records],
    )