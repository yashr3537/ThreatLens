#include <algorithm>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

#include "core/target.h"
#include "discovery/subdomain.h"
#include "network/dns.h"
#include "network/host.h"
#include "network/port.h"
#include "output/json.h"

namespace
{
void print_error(const std::string& message)
{
    std::cout << "{\"success\":false,\"error\":" << json_quote(message) << "}\n";
}

bool parse_number(const std::string& text, unsigned int minimum,
    unsigned int maximum, unsigned int& value)
{
    try
    {
        std::size_t parsed = 0;
        const unsigned long number = std::stoul(text, &parsed);
        if (parsed != text.size() || number < minimum || number > maximum)
        {
            return false;
        }
        value = static_cast<unsigned int>(number);
        return true;
    }
    catch (...)
    {
        return false;
    }
}

std::vector<std::uint16_t> parse_ports(const std::string& text)
{
    std::vector<std::uint16_t> ports;
    std::stringstream values(text);
    std::string token;

    while (std::getline(values, token, ','))
    {
        unsigned int port = 0;
        if (parse_number(token, 1, 65535, port))
        {
            ports.push_back(static_cast<std::uint16_t>(port));
        }
        else
        {
            return {};
        }
    }

    std::sort(ports.begin(), ports.end());
    ports.erase(std::unique(ports.begin(), ports.end()), ports.end());
    return ports;
}

void print_string_array(const std::vector<std::string>& values)
{
    std::cout << '[';
    for (std::size_t index = 0; index < values.size(); ++index)
    {
        if (index != 0)
        {
            std::cout << ',';
        }
        std::cout << json_quote(values[index]);
    }
    std::cout << ']';
}
}

int main(int argc, char* argv[])
{
    std::string targetInput;
    std::string wordlistPath;
    std::string portMode = "common";
    std::string portsInput;
    bool authorized = false;
    bool fullRangeConfirmed = false;
    unsigned int maxCandidates = 500;
    unsigned int dnsDelayMs = 100;
    unsigned int timeoutMs = 500;
    unsigned int concurrency = 8;
    std::unordered_set<std::string> selectedModules = {
        "target_profile", "dns", "subdomains", "hosts", "ports", "services"
    };

    for (int index = 1; index < argc; ++index)
    {
        const std::string option = argv[index];
        if (option == "--authorized")
        {
            authorized = true;
            continue;
        }
        if (option == "--full-range-confirmed")
        {
            fullRangeConfirmed = true;
            continue;
        }
        if (index + 1 >= argc)
        {
            print_error("Missing value for " + option);
            return 2;
        }

        const std::string value = argv[++index];
        if (option == "--target")
        {
            targetInput = value;
        }
        else if (option == "--wordlist")
        {
            wordlistPath = value;
        }
        else if (option == "--port-mode")
        {
            portMode = value;
        }
        else if (option == "--ports")
        {
            portsInput = value;
        }
        else if (option == "--modules")
        {
            selectedModules.clear();
            std::stringstream moduleList(value);
            std::string module;
            while (std::getline(moduleList, module, ','))
            {
                if (!module.empty())
                {
                    selectedModules.insert(module);
                }
            }
        }
        else if (option == "--max-candidates")
        {
            if (!parse_number(value, 1, 10000, maxCandidates))
            {
                print_error("max-candidates must be between 1 and 10000");
                return 2;
            }
        }
        else if (option == "--dns-delay-ms")
        {
            if (!parse_number(value, 50, 5000, dnsDelayMs))
            {
                print_error("dns-delay-ms must be between 50 and 5000");
                return 2;
            }
        }
        else if (option == "--timeout-ms")
        {
            if (!parse_number(value, 100, 10000, timeoutMs))
            {
                print_error("timeout-ms must be between 100 and 10000");
                return 2;
            }
        }
        else if (option == "--concurrency")
        {
            if (!parse_number(value, 1, 32, concurrency))
            {
                print_error("concurrency must be between 1 and 32");
                return 2;
            }
        }
        else
        {
            print_error("Unknown option: " + option);
            return 2;
        }
    }

    if (!authorized)
    {
        print_error("Authorization confirmation is required");
        return 2;
    }
    if (targetInput.empty())
    {
        print_error("Target URL is required");
        return 2;
    }
    const std::unordered_set<std::string> supportedModules = {
        "target_profile", "dns", "subdomains", "hosts", "ports", "services"
    };
    for (const std::string& module : selectedModules)
    {
        if (supportedModules.find(module) == supportedModules.end())
        {
            print_error("Unsupported Phase 1 module: " + module);
            return 2;
        }
    }
    if (selectedModules.find("target_profile") == selectedModules.end())
    {
        print_error("Target profile is required");
        return 2;
    }
    if (selectedModules.find("services") != selectedModules.end() &&
        selectedModules.find("ports") == selectedModules.end())
    {
        print_error("Service detection requires the ports module");
        return 2;
    }
    if (portMode != "common" && portMode != "list" && portMode != "full")
    {
        print_error("port-mode must be common, list, or full");
        return 2;
    }
    if (portMode == "full" && !fullRangeConfirmed)
    {
        print_error("Full TCP range requires explicit confirmation");
        return 2;
    }

    const Target target = create_target(targetInput);
    if (!target.valid)
    {
        print_error("Invalid target URL; include http:// or https://");
        return 2;
    }

    PortScanOptions portOptions;
    portOptions.timeoutMs = timeoutMs;
    portOptions.concurrency = concurrency;
    portOptions.detectBanner = true;
    if (portMode == "full")
    {
        portOptions.fullTcpRange = true;
    }
    else if (portMode == "list")
    {
        portOptions.ports = parse_ports(portsInput);
        if (portOptions.ports.empty())
        {
            print_error("A valid comma-separated port list is required for list mode");
            return 2;
        }
    }

    const bool runDns = selectedModules.find("dns") != selectedModules.end();
    const bool runSubdomains = selectedModules.find("subdomains") != selectedModules.end();
    const bool runHosts = selectedModules.find("hosts") != selectedModules.end();
    const bool runPorts = selectedModules.find("ports") != selectedModules.end();
    const bool runServices = selectedModules.find("services") != selectedModules.end();

    DnsResult dns;
    if (runDns || runHosts)
    {
        dns = resolve_dns_details(target.hostname);
    }
    else
    {
        dns.status = DnsStatus::Error;
        dns.message = "Module not selected";
    }

    SubdomainOptions subdomainOptions;
    subdomainOptions.wordlistPath = wordlistPath;
    subdomainOptions.maxCandidates = maxCandidates;
    subdomainOptions.delayMs = dnsDelayMs;
    SubdomainStats subdomainStats;
    const std::vector<SubdomainInfo> subdomains = runSubdomains
        ? discover_subdomains(target.hostname, subdomainOptions, &subdomainStats)
        : std::vector<SubdomainInfo>{};

    std::vector<HostInfo> hosts;
    if (runHosts && !dns.addresses.empty())
    {
        add_host_to_inventory(hosts, {
            target.hostname,
            dns.addresses,
            dns_status_name(dns.status)
        });
    }
    for (const SubdomainInfo& subdomain : subdomains)
    {
        if (runHosts)
        {
            add_host_to_inventory(hosts, {
                subdomain.hostname,
                subdomain.addresses,
                dns_status_name(subdomain.resolutionStatus)
            });
        }
    }

    portOptions.detectBanner = runServices;
    const std::vector<PortInfo> ports = runPorts
        ? scan_ports(target.hostname, portOptions)
        : std::vector<PortInfo>{};

    std::vector<std::string> requestedModules(selectedModules.begin(), selectedModules.end());
    std::sort(requestedModules.begin(), requestedModules.end());
    std::cout << "{\"success\":true,\"modules_requested\":";
    print_string_array(requestedModules);
    std::cout << ",\"target\":{";
    std::cout << "\"input\":" << json_quote(target.input)
        << ",\"scheme\":" << json_quote(target.scheme)
        << ",\"hostname\":" << json_quote(target.hostname)
        << ",\"path\":" << json_quote(target.path)
        << ",\"port\":" << target.port << "},\"dns\":{";
    std::cout << "\"status\":" << json_quote(dns_status_name(dns.status))
        << ",\"message\":" << json_quote(dns.message)
        << ",\"selected\":" << (runDns ? "true" : "false")
        << ",\"addresses\":";
    print_string_array(runDns ? dns.addresses : std::vector<std::string>{});

    std::cout << "},\"subdomain_discovery\":{";
    std::cout << "\"selected\":" << (runSubdomains ? "true" : "false")
        << ",\"candidates\":" << subdomainStats.candidates
        << ",\"attempted\":" << subdomainStats.attempted
        << ",\"unresolved\":" << subdomainStats.unresolved
        << ",\"timeouts\":" << subdomainStats.timedOut
        << ",\"errors\":" << subdomainStats.errors
        << ",\"invalid_words\":" << subdomainStats.invalidWords
        << ",\"stopped_on_timeout\":"
        << (subdomainStats.stoppedOnTimeout ? "true" : "false")
        << ",\"wordlist_error\":" << json_quote(subdomainStats.wordlistError)
        << ",\"results\":[";
    for (std::size_t index = 0; index < subdomains.size(); ++index)
    {
        if (index != 0)
        {
            std::cout << ',';
        }
        const SubdomainInfo& subdomain = subdomains[index];
        std::cout << "{\"hostname\":" << json_quote(subdomain.hostname)
            << ",\"status\":" << json_quote(dns_status_name(subdomain.resolutionStatus))
            << ",\"addresses\":";
        print_string_array(subdomain.addresses);
        std::cout << '}';
    }

    std::cout << "]},\"hosts\":[";
    for (std::size_t index = 0; runHosts && index < hosts.size(); ++index)
    {
        if (index != 0)
        {
            std::cout << ',';
        }
        const HostInfo& host = hosts[index];
        std::cout << "{\"hostname\":" << json_quote(host.hostname)
            << ",\"status\":" << json_quote(host.resolutionStatus)
            << ",\"addresses\":";
        print_string_array(host.addresses);
        std::cout << '}';
    }

    std::cout << "],\"ports\":[";
    for (std::size_t index = 0; runPorts && index < ports.size(); ++index)
    {
        if (index != 0)
        {
            std::cout << ',';
        }
        const PortInfo& item = ports[index];
        std::cout << "{\"hostname\":" << json_quote(item.hostname)
            << ",\"address\":" << json_quote(item.address)
            << ",\"port\":" << item.port
            << ",\"protocol\":" << json_quote(item.protocol)
            << ",\"state\":" << json_quote(item.state)
            << ",\"service\":" << json_quote(item.service)
            << ",\"version\":" << json_quote(item.version) << '}';
    }
    std::cout << "]}\n";
    return 0;
}