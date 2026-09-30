#ifndef DNS_H
#define DNS_H

#include <string>
#include <vector>

enum class DnsStatus
{
	Resolved,
	NotFound,
	Timeout,
	Error
};

struct DnsResult
{
	std::vector<std::string> addresses;
	DnsStatus status = DnsStatus::Error;
	std::string message;
};

DnsResult resolve_dns_details(const std::string& hostname);
std::string dns_status_name(DnsStatus status);

std::vector<std::string> resolve_dns(const std::string& hostname);

#endif