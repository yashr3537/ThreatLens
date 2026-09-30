#ifndef PORT_H
#define PORT_H

#include <string>
#include <cstdint>
#include <vector>

struct PortInfo
{
    std::string hostname;
    std::string address;
    int port;
    std::string protocol;
    std::string state;
    std::string service;
    std::string version;
};

struct PortScanOptions
{
    std::vector<std::uint16_t> ports;
    bool fullTcpRange = false;
    unsigned int timeoutMs = 500;
    unsigned int concurrency = 8;
    bool detectBanner = true;
};

std::vector<PortInfo> scan_ports(
    const std::string& hostname,
    const PortScanOptions& options = PortScanOptions{}
);

std::vector<std::uint16_t> common_tcp_ports();

#endif