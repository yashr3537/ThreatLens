import asyncio
import json
import os
from pathlib import Path
import shutil
from datetime import datetime
from time import monotonic

from ..scan_config import PHASE1_MODULES, PROVIDER_MODULES, ScanConfig
from ..providers.dns_records import lookup_dns_records
from ..providers.http_analysis import analyze_headers, detect_technologies, inspect_cookies
from ..providers.http_client import http_probe
from ..providers.result import ToolResult
from ..providers.tls import inspect_tls
from ..providers.web_discovery import discover_directories, discover_web_surface
from ..scan_store import delete_scan, load_scans, save_scan
from ..tool_history import get_tool_history as _get_tool_history, record_tool_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCANNER_PATH = PROJECT_ROOT / "scanner_gui.exe"
BUILD_SOURCES = [
    "scanner/main.cpp",
    "scanner/core/target.cpp",
    "scanner/network/dns.cpp",
    "scanner/network/host.cpp",
    "scanner/network/port.cpp",
    "scanner/discovery/subdomain.cpp",
    "scanner/output/json.cpp",
]
BUILD_COMMAND = (
    'C:\\msys64\\ucrt64\\bin\\g++.exe -std=c++17 -Wall -Wextra '
    'scanner/main.cpp scanner/core/target.cpp scanner/network/dns.cpp '
    'scanner/network/host.cpp scanner/network/port.cpp '
    'scanner/discovery/subdomain.cpp scanner/output/json.cpp '
    '-lws2_32 -pthread -o "C:\\ThreatLens\\scanner_gui.exe"'
)
_REPORT_HISTORY = load_scans()
_LATEST_REPORT = _REPORT_HISTORY[-1] if _REPORT_HISTORY else None


def save_latest_report(report):
    global _LATEST_REPORT
    _LATEST_REPORT = report


def get_latest_report():
    return _LATEST_REPORT


def get_report_history():
    return list(_REPORT_HISTORY)


def get_session_tool_history():
    return _get_tool_history()


def delete_scan_report(scan_id):
    global _LATEST_REPORT
    deleted = delete_scan(scan_id)
    if deleted:
        _REPORT_HISTORY[:] = [
            report for report in _REPORT_HISTORY
            if report.get("_session", {}).get("scan_id") != scan_id
        ]
        _LATEST_REPORT = _REPORT_HISTORY[-1] if _REPORT_HISTORY else None
    return deleted


def _tool_result_dict(result, tool_name=None):
    output = result.to_dict()
    if tool_name:
        output["tool"] = tool_name
    return output


async def _run_selected_providers(config, data):
    selected = config.modules & PROVIDER_MODULES
    results = {}
    target = config.target_url
    profile = data.get("target", {})
    hostname = profile.get("hostname", "")

    async def run_provider(name, function, *arguments):
        try:
            result = await asyncio.to_thread(function, *arguments)
        except Exception as error:
            result = ToolResult(name, target, "failed", errors=[str(error)])
        results[name] = _tool_result_dict(result, name)

    if "dns_records" in selected:
        await run_provider("dns_records", lookup_dns_records, hostname)

    http_modules = {"http_probe", "url_probe", "endpoints", "headers", "cookies", "technology"}
    http_result = None
    if selected & http_modules:
        include_body = bool(selected & {"http_probe", "url_probe", "endpoints", "technology"})
        try:
            http_result = await asyncio.to_thread(http_probe, target, include_body)
        except Exception as error:
            http_result = ToolResult("http_probe", target, "failed", errors=[str(error)])
        if "http_probe" in selected:
            results["http_probe"] = _tool_result_dict(http_result)
        if "url_probe" in selected:
            results["url_probe"] = _tool_result_dict(http_result, "url_probe")
        for module, function in (
            ("endpoints", discover_web_surface),
            ("headers", analyze_headers),
            ("cookies", inspect_cookies),
            ("technology", detect_technologies),
        ):
            if module in selected:
                try:
                    derived = function(target, http_result)
                except Exception as error:
                    derived = ToolResult(module, target, "failed", errors=[str(error)])
                results[module] = _tool_result_dict(derived)
        if http_result is not None:
            http_result.data.pop("_body_for_analysis", None)

    if "directory" in selected:
        await run_provider(
            "directory",
            discover_directories,
            target,
            config.directory_wordlist_path,
            min(config.max_candidates, 100),
            max(config.dns_delay_ms, 250),
        )

    if "tls" in selected:
        if profile.get("scheme") != "https":
            result = ToolResult("tls", target, "failed", errors=["TLS inspection requires an HTTPS target."])
            results["tls"] = _tool_result_dict(result)
        else:
            tls_target = f"https://{hostname}:{profile.get('port', 443)}"
            await run_provider("tls", inspect_tls, tls_target, 5)

    return results


async def _ensure_scanner_built():
    source_paths = [PROJECT_ROOT / source for source in BUILD_SOURCES]
    missing_sources = [str(path) for path in source_paths if not path.is_file()]
    if missing_sources:
        raise FileNotFoundError("Scanner source file missing: " + ", ".join(missing_sources))

    newest_source = max(path.stat().st_mtime for path in source_paths)
    if SCANNER_PATH.is_file() and SCANNER_PATH.stat().st_mtime >= newest_source:
        return

    configured_compiler = Path(r"C:\msys64\ucrt64\bin\g++.exe")
    compiler = str(configured_compiler) if configured_compiler.is_file() else shutil.which("g++")
    if not compiler:
        raise FileNotFoundError(
            "C++17 compiler g++ was not found. Install MSYS2 UCRT64 GCC and reopen the GUI.\n"
            f"Expected build command: {BUILD_COMMAND}"
        )

    command = [compiler, "-std=c++17", "-Wall", "-Wextra"]
    command.extend(str(path.relative_to(PROJECT_ROOT)) for path in source_paths)
    command.extend(["-lws2_32", "-pthread", "-o", str(SCANNER_PATH)])

    build = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(PROJECT_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(build.communicate(), timeout=300)
    except asyncio.TimeoutError as error:
        build.kill()
        await build.communicate()
        raise TimeoutError("Building the C++ scanner timed out.") from error

    if build.returncode != 0 or not SCANNER_PATH.is_file():
        details = (stderr or stdout).decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            "Could not build scanner_gui.exe. Compiler output:\n"
            + (details or "Compiler exited without creating the executable.")
        )


async def run_phase1_scan(
    url,
    authorized=False,
    wordlist_path="",
    max_candidates=500,
    dns_delay_ms=100,
    port_mode="common",
    ports="",
    timeout_ms=500,
    concurrency=8,
    full_range_confirmed=False,
    process_timeout=900,
    modules=None,
    config=None,
    directory_wordlist_path="",
    history_kind="scan",
):
    if config is None:
        config = ScanConfig(
            target_url=url or "",
            authorized=authorized,
            modules=frozenset(PHASE1_MODULES if modules is None else modules),
            wordlist_path=wordlist_path,
            directory_wordlist_path=directory_wordlist_path,
            max_candidates=max_candidates,
            dns_delay_ms=dns_delay_ms,
            port_mode=port_mode,
            ports=ports,
            timeout_ms=timeout_ms,
            concurrency=concurrency,
            full_range_confirmed=full_range_confirmed,
        )
    config.validate()

    started_at = datetime.now().astimezone()
    started = monotonic()
    await _ensure_scanner_built()

    command = [
        str(SCANNER_PATH),
        "--target", config.target_url.strip(),
        "--max-candidates", str(config.max_candidates),
        "--dns-delay-ms", str(config.dns_delay_ms),
        "--port-mode", config.port_mode,
        "--timeout-ms", str(config.timeout_ms),
        "--concurrency", str(config.concurrency),
        "--modules", ",".join(sorted(config.modules & PHASE1_MODULES)),
    ]
    command.append("--authorized")
    if config.wordlist_path.strip():
        command.extend(["--wordlist", config.wordlist_path.strip()])
    if "ports" in config.modules and config.port_mode == "list":
        command.extend(["--ports", config.ports.strip()])
    if "ports" in config.modules and config.port_mode == "full" and config.full_range_confirmed:
        command.append("--full-range-confirmed")

    environment = os.environ.copy()
    mingw_runtime = Path(r"C:\msys64\ucrt64\bin")
    if mingw_runtime.is_dir():
        environment["PATH"] = str(mingw_runtime) + os.pathsep + environment.get("PATH", "")

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(SCANNER_PATH.parent),
        env=environment,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=process_timeout,
        )
    except asyncio.TimeoutError as error:
        process.kill()
        await process.communicate()
        raise TimeoutError("Scanner timed out. Reduce wordlist size or scan scope.") from error
    except asyncio.CancelledError:
        process.kill()
        await process.communicate()
        raise

    output = stdout.decode("utf-8", errors="replace").strip()
    error_output = stderr.decode("utf-8", errors="replace").strip()

    try:
        data = json.loads(output)
    except json.JSONDecodeError as error:
        detail = error_output or output or "Scanner returned no output."
        raise RuntimeError(f"Could not parse scanner output: {detail}") from error

    if process.returncode != 0 or not data.get("success"):
        raise RuntimeError(data.get("error") or error_output or "Scanner failed.")

    data["modules_requested"] = sorted(config.modules)
    provider_results = await _run_selected_providers(config, data)
    data["tool_results"] = provider_results
    module_status = {
        "target_profile": "completed",
        "dns": data.get("dns", {}).get("status", "not_selected") if "dns" in config.modules else "not_selected",
        "subdomains": "completed" if "subdomains" in config.modules else "not_selected",
        "hosts": "completed" if "hosts" in config.modules else "not_selected",
        "ports": "completed" if "ports" in config.modules else "not_selected",
        "services": "completed" if "services" in config.modules else "not_selected",
    }
    module_status.update({name: result.get("status", "failed") for name, result in provider_results.items()})
    data["module_status"] = module_status

    data["_session"] = {
        "started_at": started_at.isoformat(timespec="seconds"),
        "duration_seconds": round(monotonic() - started, 2),
        "scan_profile": config.port_mode,
        "modules": sorted(config.modules),
        "history_kind": history_kind,
    }
    if history_kind == "tool":
        record_tool_run(data)
    else:
        try:
            save_scan(data)
        except OSError as error:
            data["_session"]["persistence_warning"] = str(error)
        save_latest_report(data)
        _REPORT_HISTORY.append(data)
        del _REPORT_HISTORY[:-100]
    return data