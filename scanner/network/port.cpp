#include <winsock2.h>
#include <ws2tcpip.h>

#include "port.h"

#include "dns.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <cctype>
#include <cstring>
#include <mutex>
#include <thread>
#include <unordered_set>

#ifdef _MSC_VER
#pragma comment(lib, "ws2_32.lib")
#endif

namespace
{
struct Endpoint
{
    std::string address;
    int family;
    sockaddr_storage socketAddress{};
    int addressLength = 0;
};

std::string service_for_port(unsigned short port)
{
    switch (port)
    {
    case 21: return "FTP";
    case 22: return "SSH";
    case 23: return "Telnet";
    case 25: return "SMTP";
    case 53: return "DNS";
    case 80: return "HTTP";
    case 110: return "POP3";
    case 143: return "IMAP";
    case 443: return "HTTPS";
    case 445: return "SMB";
    case 465: return "SMTPS";
    case 587: return "SMTP submission";
    case 993: return "IMAPS";
    case 995: return "POP3S";
    case 1433: return "Microsoft SQL Server";
    case 3306: return "MySQL";
    case 3389: return "RDP";
    case 5432: return "PostgreSQL";
    case 5900: return "VNC";
    case 6379: return "Redis";
    case 8080: return "HTTP alternate";
    case 8443: return "HTTPS alternate";
    case 9200: return "Elasticsearch";
    default: return "unknown";
    }
}

bool connect_with_timeout(SOCKET socketHandle, const Endpoint& endpoint,
    unsigned short port, unsigned int timeoutMs)
{
    u_long nonBlocking = 1;
    if (ioctlsocket(socketHandle, FIONBIO, &nonBlocking) != 0)
    {
        return false;
    }

    sockaddr_storage destination = endpoint.socketAddress;
    if (endpoint.family == AF_INET)
    {
        reinterpret_cast<sockaddr_in*>(&destination)->sin_port = htons(port);
    }
    else
    {
        reinterpret_cast<sockaddr_in6*>(&destination)->sin6_port = htons(port);
    }

    const int connectionResult = connect(
        socketHandle,
        reinterpret_cast<const sockaddr*>(&destination),
        endpoint.addressLength
    );
    if (connectionResult == 0)
    {
        return true;
    }

    const int connectError = WSAGetLastError();
    if (connectError != WSAEWOULDBLOCK &&
        connectError != WSAEINPROGRESS &&
        connectError != WSAEALREADY)
    {
        return false;
    }

    fd_set writeSet;
    FD_ZERO(&writeSet);
    FD_SET(socketHandle, &writeSet);

    timeval timeout{};
    timeout.tv_sec = static_cast<long>(timeoutMs / 1000);
    timeout.tv_usec = static_cast<long>((timeoutMs % 1000) * 1000);

    if (select(0, nullptr, &writeSet, nullptr, &timeout) <= 0)
    {
        return false;
    }

    int socketError = 0;
    int errorLength = sizeof(socketError);
    return getsockopt(
        socketHandle,
        SOL_SOCKET,
        SO_ERROR,
        reinterpret_cast<char*>(&socketError),
        &errorLength
    ) == 0 && socketError == 0;
}

std::string read_service_banner(SOCKET socketHandle, const std::string& service)
{
    u_long blocking = 0;
    ioctlsocket(socketHandle, FIONBIO, &blocking);

    const DWORD receiveTimeout = 250;
    setsockopt(
        socketHandle,
        SOL_SOCKET,
        SO_RCVTIMEO,
        reinterpret_cast<const char*>(&receiveTimeout),
        sizeof(receiveTimeout)
    );

    if (service == "HTTP" || service == "HTTP alternate")
    {
        static const char request[] = "HEAD / HTTP/1.0\r\nConnection: close\r\n\r\n";
        send(socketHandle, request, static_cast<int>(sizeof(request) - 1), 0);
    }

    std::array<char, 512> buffer{};
    const int received = recv(socketHandle, buffer.data(), static_cast<int>(buffer.size()), 0);
    if (received <= 0)
    {
        return {};
    }

    std::string banner;
    for (int index = 0; index < received && banner.size() < 160; ++index)
    {
        const unsigned char character = static_cast<unsigned char>(buffer[index]);
        if (std::isprint(character) || character == '\r' || character == '\n' || character == '\t')
        {
            banner.push_back(static_cast<char>(character));
        }
    }

    const std::size_t end = banner.find_first_of("\r\n");
    if (end != std::string::npos)
    {
        banner.resize(end);
    }

    return banner;
}

Endpoint make_endpoint(const std::string& address)
{
    Endpoint endpoint{};
    endpoint.address = address;

    sockaddr_in ipv4{};
    if (InetPtonA(AF_INET, address.c_str(), &ipv4.sin_addr) == 1)
    {
        ipv4.sin_family = AF_INET;
        endpoint.family = AF_INET;
        endpoint.addressLength = sizeof(ipv4);
        std::memcpy(&endpoint.socketAddress, &ipv4, sizeof(ipv4));
        return endpoint;
    }

    sockaddr_in6 ipv6{};
    if (InetPtonA(AF_INET6, address.c_str(), &ipv6.sin6_addr) == 1)
    {
        ipv6.sin6_family = AF_INET6;
        endpoint.family = AF_INET6;
        endpoint.addressLength = sizeof(ipv6);
        std::memcpy(&endpoint.socketAddress, &ipv6, sizeof(ipv6));
        return endpoint;
    }

    endpoint.family = AF_UNSPEC;
    return endpoint;
}
}

std::vector<std::uint16_t> common_tcp_ports()
{
    return {
        21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
        465, 587, 993, 995, 1433, 3306, 3389, 5432, 5900,
        6379, 8080, 8443, 9200
    };
}

std::vector<PortInfo> scan_ports(
    const std::string& hostname,
    const PortScanOptions& options)
{
    const DnsResult dns = resolve_dns_details(hostname);
    if (dns.addresses.empty())
    {
        return {};
    }

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
    {
        return {};
    }

    std::vector<std::uint16_t> ports = options.ports;
    if (options.fullTcpRange)
    {
        ports.clear();
        ports.reserve(65535);
        for (unsigned int port = 1; port <= 65535; ++port)
        {
            ports.push_back(static_cast<std::uint16_t>(port));
        }
    }
    else if (ports.empty())
    {
        ports = common_tcp_ports();
    }

    std::sort(ports.begin(), ports.end());
    ports.erase(std::unique(ports.begin(), ports.end()), ports.end());

    std::vector<Endpoint> endpoints;
    for (const std::string& address : dns.addresses)
    {
        Endpoint endpoint = make_endpoint(address);
        if (endpoint.family != AF_UNSPEC)
        {
            endpoints.push_back(endpoint);
        }
    }

    std::vector<PortInfo> found;
    if (endpoints.empty() || ports.empty())
    {
        WSACleanup();
        return found;
    }

    const std::size_t taskCount = endpoints.size() * ports.size();
    std::atomic<std::size_t> nextTask{0};
    std::mutex resultMutex;
    const unsigned int workerCount = std::max(1U, std::min(options.concurrency, 32U));
    const unsigned int timeoutMs = std::max(100U, std::min(options.timeoutMs, 10000U));

    auto worker = [&]()
    {
        while (true)
        {
            const std::size_t task = nextTask.fetch_add(1);
            if (task >= taskCount)
            {
                return;
            }

            const Endpoint& endpoint = endpoints[task / ports.size()];
            const unsigned short port = ports[task % ports.size()];
            SOCKET socketHandle = socket(endpoint.family, SOCK_STREAM, IPPROTO_TCP);
            if (socketHandle == INVALID_SOCKET)
            {
                continue;
            }

            const bool isOpen = connect_with_timeout(socketHandle, endpoint, port, timeoutMs);
            if (isOpen)
            {
                std::string service = service_for_port(port);
                std::string version;
                if (options.detectBanner)
                {
                    version = read_service_banner(socketHandle, service);
                    if (service == "unknown" && version.rfind("SSH-", 0) == 0)
                    {
                        service = "SSH";
                    }
                    else if (service == "unknown" && version.rfind("HTTP/", 0) == 0)
                    {
                        service = "HTTP";
                    }
                    else if (service == "unknown" && version.rfind("220 ", 0) == 0)
                    {
                        service = "FTP/SMTP (banner-based)";
                    }
                }

                PortInfo result{
                    hostname,
                    endpoint.address,
                    port,
                    "TCP",
                    "open",
                    service,
                    version
                };
                std::lock_guard<std::mutex> lock(resultMutex);
                found.push_back(std::move(result));
            }

            closesocket(socketHandle);
        }
    };

    std::vector<std::thread> workers;
    workers.reserve(workerCount);
    for (unsigned int index = 0; index < workerCount; ++index)
    {
        workers.emplace_back(worker);
    }
    for (std::thread& thread : workers)
    {
        thread.join();
    }

    std::sort(found.begin(), found.end(), [](const PortInfo& left, const PortInfo& right)
    {
        if (left.address != right.address)
        {
            return left.address < right.address;
        }
        return left.port < right.port;
    });
    found.erase(std::unique(found.begin(), found.end(), [](const PortInfo& left, const PortInfo& right)
    {
        return left.address == right.address && left.port == right.port;
    }), found.end());

    WSACleanup();
    return found;
}