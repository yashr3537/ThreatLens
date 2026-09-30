#include "host.h"

#include "dns.h"

#include <algorithm>
#include <cctype>
#include <unordered_set>

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
}

void add_host_to_inventory(std::vector<HostInfo>& inventory, const HostInfo& host)
{
    const std::string normalizedHostname = lowercase(host.hostname);
    auto existing = std::find_if(inventory.begin(), inventory.end(), [&](const HostInfo& item)
    {
        return lowercase(item.hostname) == normalizedHostname;
    });

    if (existing == inventory.end())
    {
        inventory.push_back({host.hostname, {}, host.resolutionStatus});
        existing = inventory.end() - 1;
    }
    else if (existing->resolutionStatus != "resolved" && host.resolutionStatus == "resolved")
    {
        existing->resolutionStatus = "resolved";
    }

    std::unordered_set<std::string> seen;
    for (const std::string& address : existing->addresses)
    {
        seen.insert(lowercase(address));
    }
    for (const std::string& address : host.addresses)
    {
        if (seen.insert(lowercase(address)).second)
        {
            existing->addresses.push_back(address);
        }
    }
}

std::vector<HostInfo> discover_hosts(const std::vector<std::string>& hostnames)
{
    std::vector<HostInfo> inventory;
    std::unordered_set<std::string> queried;

    for (const std::string& hostname : hostnames)
    {
        if (hostname.empty() || !queried.insert(lowercase(hostname)).second)
        {
            continue;
        }

        const DnsResult dns = resolve_dns_details(hostname);
        add_host_to_inventory(inventory, {
            hostname,
            dns.addresses,
            dns_status_name(dns.status)
        });
    }

    return inventory;
}

std::vector<std::string> discover_hosts(const std::string& hostname)
{
    return resolve_dns(hostname);
}