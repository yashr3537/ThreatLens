#include <winsock2.h>

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "core/target.h"
#include "network/dns.h"
#include "network/host.h"
#include "network/port.h"
#include "discovery/subdomain.h"

namespace
{
std::string lowercase(std::string value)
{
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return value;
}

std::string prompt(const std::string& message)
{
    std::cout << message;
    std::string value;
    std::getline(std::cin, value);
    return value;
}

unsigned int prompt_number(const std::string& message, unsigned int fallback,
    unsigned int minimum, unsigned int maximum)
{
    const std::string input = prompt(message);
    if (input.empty())
    {
        return fallback;
    }

    try
    {
        std::size_t parsed = 0;
        const unsigned long value = std::stoul(input, &parsed);
        if (parsed != input.size())
        {
            return fallback;
        }
        return static_cast<unsigned int>(std::max<unsigned long>(
            minimum, std::min<unsigned long>(value, maximum)));
    }
    catch (...)
    {
        return fallback;
    }
}

std::vector<std::uint16_t> parse_port_list(const std::string& input)
{
    std::vector<std::uint16_t> ports;
    std::stringstream values(input);
    std::string token;

    while (std::getline(values, token, ','))
    {
        std::stringstream number(token);
        unsigned int port = 0;
        char extra = 0;
        if ((number >> port) && !(number >> extra) && port > 0 && port <= 65535)
        {
            ports.push_back(static_cast<std::uint16_t>(port));
        }
    }

    std::sort(ports.begin(), ports.end());
    ports.erase(std::unique(ports.begin(), ports.end()), ports.end());
    return ports;
}
}

int main()
{
    const std::string input = prompt("Enter target URL (http:// or https://): ");
    const Target target = create_target(input);

    if (!target.valid)
    {
        std::cout << "\nInvalid target. Include http:// or https:// and a hostname.\n";
        return 1;
    }

    std::cout << "\nThreatLens Phase 1 performs DNS discovery and TCP connection checks.\n"
        << "Continue only for a system you own or are authorized to assess.\n";
    if (lowercase(prompt("Confirm authorization (yes/no): ")) != "yes")
    {
        std::cout << "Scan cancelled.\n";
        return 0;
    }

    std::cout << "\n========== TARGET PROFILE ==========\n";
    std::cout << "Input    : " << target.input << "\n";
    std::cout << "Scheme   : " << target.scheme << "\n";
    std::cout << "Hostname : " << target.hostname << "\n";
    std::cout << "Path     : " << target.path << "\n";
    std::cout << "Port     : " << target.port << "\n";

    const DnsResult dns = resolve_dns_details(target.hostname);
    std::cout << "\n========== DNS INFORMATION ==========\n";
    std::cout << "Status   : " << dns_status_name(dns.status) << "\n";
    if (dns.addresses.empty())
    {
        std::cout << "Details  : " << dns.message << "\n";
    }
    for (const std::string& address : dns.addresses)
    {
        std::cout << "Address  : " << address << "\n";
    }

    SubdomainOptions subdomainOptions;
    subdomainOptions.wordlistPath = prompt(
        "Subdomain wordlist path (blank uses built-in list): ");
    subdomainOptions.maxCandidates = prompt_number(
        "Maximum DNS candidates (default 500, max 10000): ", 500, 1, 10000);
    subdomainOptions.delayMs = prompt_number(
        "Delay between DNS queries in ms (default 100, min 50): ", 100, 50, 5000);

    SubdomainStats subdomainStats;
    const std::vector<SubdomainInfo> subdomains = discover_subdomains(
        target.hostname,
        subdomainOptions,
        &subdomainStats
    );

    std::cout << "\n========== SUBDOMAIN DISCOVERY ==========\n";
    std::cout << "Candidates : " << subdomainStats.candidates << "\n";
    std::cout << "Attempted  : " << subdomainStats.attempted << "\n";
    std::cout << "Unresolved : " << subdomainStats.unresolved << "\n";
    std::cout << "Timeouts   : " << subdomainStats.timedOut << "\n";
    std::cout << "Errors     : " << subdomainStats.errors << "\n";
    std::cout << "Invalid labels skipped: " << subdomainStats.invalidWords << "\n";
    if (!subdomainStats.wordlistError.empty())
    {
        std::cout << "Wordlist   : " << subdomainStats.wordlistError << "\n";
    }
    if (subdomainStats.stoppedOnTimeout)
    {
        std::cout << "Discovery stopped after a DNS timeout to avoid excess queries.\n";
    }

    if (subdomains.empty())
    {
        std::cout << "No resolving subdomains found.\n";
    }
    else
    {
        for (const SubdomainInfo& subdomain : subdomains)
        {
            std::cout << subdomain.hostname << " | status: "
                << dns_status_name(subdomain.resolutionStatus) << "\n";
            for (const std::string& address : subdomain.addresses)
            {
                std::cout << "  IP: " << address << "\n";
            }
        }
    }

    std::vector<HostInfo> hosts;
    if (!dns.addresses.empty())
    {
        add_host_to_inventory(hosts, {
            target.hostname,
            dns.addresses,
            dns_status_name(dns.status)
        });
    }
    for (const SubdomainInfo& subdomain : subdomains)
    {
        add_host_to_inventory(hosts, {
            subdomain.hostname,
            subdomain.addresses,
            dns_status_name(subdomain.resolutionStatus)
        });
    }

    std::cout << "\n========== IP / HOST DISCOVERY ==========\n";
    if (hosts.empty())
    {
        std::cout << "No resolved hosts in inventory.\n";
    }
    for (const HostInfo& host : hosts)
    {
        std::cout << host.hostname << " | status: " << host.resolutionStatus << "\n";
        for (const std::string& address : host.addresses)
        {
            std::cout << "  IP: " << address << "\n";
        }
    }

    PortScanOptions portOptions;
    const std::string portMode = lowercase(prompt(
        "TCP ports: [c]ommon (default), [l]ist, or [f]ull range: "));
    bool runPortScan = true;

    if (portMode == "f" || portMode == "full")
    {
        std::cout << "Full TCP scan checks ports 1-65535 and may take a while.\n";
        if (lowercase(prompt("Confirm full-range scan (yes/no): ")) == "yes")
        {
            portOptions.fullTcpRange = true;
        }
        else
        {
            std::cout << "Port scan skipped.\n";
            runPortScan = false;
        }
    }
    else if (portMode == "l" || portMode == "list")
    {
        portOptions.ports = parse_port_list(prompt(
            "Enter TCP ports, comma-separated (1-65535): "));
        if (portOptions.ports.empty())
        {
            std::cout << "No valid ports entered; using common ports.\n";
        }
    }

    portOptions.timeoutMs = prompt_number(
        "TCP timeout in ms (default 500, range 100-10000): ", 500, 100, 10000);
    portOptions.concurrency = prompt_number(
        "Concurrent connections (default 8, range 1-32): ", 8, 1, 32);

    std::cout << "\n========== PORT & SERVICE INVENTORY ==========\n";
    if (runPortScan)
    {
        const std::vector<PortInfo> ports = scan_ports(target.hostname, portOptions);
        if (ports.empty())
        {
            std::cout << "No open TCP ports found (or the target did not resolve).\n";
        }
        for (const PortInfo& item : ports)
        {
            std::cout << item.hostname << " (" << item.address << ") "
                << item.port << "/" << item.protocol << " " << item.state
                << " | service: " << item.service;
            if (!item.version.empty())
            {
                std::cout << " | banner: " << item.version;
            }
            std::cout << "\n";
        }
    }

    return 0;
}