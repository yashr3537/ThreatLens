from dataclasses import dataclass, field


PHASE1_MODULES = frozenset({
    "target_profile",
    "dns",
    "subdomains",
    "hosts",
    "ports",
    "services",
})
PROVIDER_MODULES = frozenset({
    "dns_records",
    "http_probe",
    "url_probe",
    "endpoints",
    "directory",
    "tls",
    "headers",
    "cookies",
    "technology",
})
SUPPORTED_MODULES = PHASE1_MODULES | PROVIDER_MODULES


@dataclass(frozen=True)
class ScanConfig:
    target_url: str
    authorized: bool
    modules: frozenset[str] = field(default_factory=lambda: PHASE1_MODULES)
    wordlist_path: str = ""
    directory_wordlist_path: str = ""
    max_candidates: int = 500
    dns_delay_ms: int = 100
    port_mode: str = "common"
    ports: str = ""
    timeout_ms: int = 500
    concurrency: int = 8
    full_range_confirmed: bool = False

    def validate(self):
        if not self.authorized:
            raise PermissionError("Authorization confirmation is required before scanning.")
        if not self.target_url.strip():
            raise ValueError("Target URL is required.")
        unknown = self.modules - SUPPORTED_MODULES
        if unknown:
            raise ValueError("Unsupported scan module(s): " + ", ".join(sorted(unknown)))
        if "target_profile" not in self.modules:
            raise ValueError("Target profile is required for every scan.")
        if "services" in self.modules and "ports" not in self.modules:
            raise ValueError("Service detection requires port discovery to be selected.")
        if "directory" in self.modules and not self.directory_wordlist_path.strip():
            raise ValueError("Directory discovery requires a user-provided wordlist.")
        if not 1 <= self.max_candidates <= 10000:
            raise ValueError("DNS candidate limit must be between 1 and 10000.")
        if not 50 <= self.dns_delay_ms <= 5000:
            raise ValueError("DNS delay must be between 50 and 5000 ms.")
        if not 100 <= self.timeout_ms <= 10000:
            raise ValueError("TCP timeout must be between 100 and 10000 ms.")
        if not 1 <= self.concurrency <= 32:
            raise ValueError("Concurrency must be between 1 and 32 workers.")
        if "ports" not in self.modules:
            return
        if self.port_mode not in {"common", "list", "full"}:
            raise ValueError("Port mode must be common, list, or full.")
        if self.port_mode == "list" and not self.ports.strip():
            raise ValueError("Enter one or more ports for custom-list mode.")
        if self.port_mode == "full" and not self.full_range_confirmed:
            raise ValueError("Full TCP range requires explicit confirmation.")