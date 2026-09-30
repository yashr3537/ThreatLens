#ifndef HOST_H
#define HOST_H

#include <string>
#include <vector>

struct HostInfo
{
    std::string hostname;
    std::vector<std::string> addresses;
    std::string resolutionStatus;
};

std::vector<HostInfo> discover_hosts(const std::vector<std::string>& hostnames);
std::vector<std::string> discover_hosts(const std::string& hostname);
void add_host_to_inventory(std::vector<HostInfo>& inventory, const HostInfo& host);

#endif