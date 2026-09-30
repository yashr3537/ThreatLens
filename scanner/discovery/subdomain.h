#ifndef SUBDOMAIN_H
#define SUBDOMAIN_H

#include <cstddef>
#include <string>
#include <vector>

#include "../network/dns.h"

struct SubdomainInfo
{
    std::string hostname;
    std::vector<std::string> addresses;
    DnsStatus resolutionStatus = DnsStatus::Resolved;
};

struct SubdomainOptions
{
    std::string wordlistPath;
    std::vector<std::string> words;
    std::size_t maxCandidates = 500;
    unsigned int delayMs = 100;
};

struct SubdomainStats
{
    std::size_t candidates = 0;
    std::size_t attempted = 0;
    std::size_t unresolved = 0;
    std::size_t timedOut = 0;
    std::size_t errors = 0;
    std::size_t invalidWords = 0;
    bool stoppedOnTimeout = false;
    std::string wordlistError;
};

std::vector<SubdomainInfo> discover_subdomains(
    const std::string& hostname,
    const SubdomainOptions& options,
    SubdomainStats* stats = nullptr
);

std::vector<std::string> discover_subdomains(const std::string& hostname);

#endif