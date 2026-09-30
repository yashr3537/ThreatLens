#include <winsock2.h>
#include <ws2tcpip.h>

#include "dns.h"

#include <unordered_set>

#ifdef _MSC_VER
#pragma comment(lib, "ws2_32.lib")
#endif

DnsResult resolve_dns_details(const std::string& hostname)
{
    DnsResult dns;

    WSADATA wsaData;

    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
    {
        dns.status = DnsStatus::Error;
        dns.message = "Winsock initialization failed";
        return dns;
    }

    addrinfo hints{};
    addrinfo* result = nullptr;

    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    const int lookupStatus = getaddrinfo(hostname.c_str(), nullptr, &hints, &result);

    if (lookupStatus == 0)
    {
        std::unordered_set<std::string> seen;

        for (addrinfo* current = result; current != nullptr; current = current->ai_next)
        {
            char ip[INET6_ADDRSTRLEN] = {};

            void* address = nullptr;

            if (current->ai_family == AF_INET)
            {
                address = &reinterpret_cast<sockaddr_in*>(current->ai_addr)->sin_addr;
            }
            else if (current->ai_family == AF_INET6)
            {
                address = &reinterpret_cast<sockaddr_in6*>(current->ai_addr)->sin6_addr;
            }

            if (address != nullptr)
            {
                if (inet_ntop(current->ai_family, address, ip, sizeof(ip)) != nullptr)
                {
                    if (seen.insert(ip).second)
                    {
                        dns.addresses.emplace_back(ip);
                    }
                }
            }
        }

        dns.status = dns.addresses.empty() ? DnsStatus::NotFound : DnsStatus::Resolved;
        dns.message = dns.addresses.empty() ? "No IPv4 or IPv6 address found" : "Resolved";
    }
    else if (lookupStatus == EAI_AGAIN || lookupStatus == WSATRY_AGAIN)
    {
        dns.status = DnsStatus::Timeout;
        dns.message = "DNS lookup timed out or was temporarily unavailable";
    }
    else if (lookupStatus == EAI_NONAME || lookupStatus == WSAHOST_NOT_FOUND || lookupStatus == WSANO_DATA)
    {
        dns.status = DnsStatus::NotFound;
        dns.message = "Hostname did not resolve";
    }
    else
    {
        dns.status = DnsStatus::Error;
        dns.message = "DNS lookup failed";
    }

    if (result != nullptr)
    {
        freeaddrinfo(result);
    }

    WSACleanup();

    return dns;
}

std::string dns_status_name(DnsStatus status)
{
    switch (status)
    {
    case DnsStatus::Resolved:
        return "resolved";
    case DnsStatus::NotFound:
        return "not resolved";
    case DnsStatus::Timeout:
        return "timeout";
    case DnsStatus::Error:
        return "error";
    }

    return "error";
}

std::vector<std::string> resolve_dns(const std::string& hostname)
{
    return resolve_dns_details(hostname).addresses;
}