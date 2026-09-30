#include "subdomain.h"

#include <chrono>
#include <cctype>
#include <fstream>
#include <thread>
#include <unordered_set>

namespace
{
std::string trim(const std::string& value)
{
    const std::size_t first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos)
    {
        return {};
    }

    const std::size_t last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

bool normalize_label(std::string& label)
{
    label = trim(label);
    if (label.rfind("*.", 0) == 0)
    {
        label.erase(0, 2);
    }

    if (label.empty() || label.size() > 63 || label.front() == '-' || label.back() == '-')
    {
        return false;
    }

    for (char& character : label)
    {
        const unsigned char value = static_cast<unsigned char>(character);
        if (!std::isalnum(value) && character != '-')
        {
            return false;
        }
        character = static_cast<char>(std::tolower(value));
    }

    return true;
}

const std::vector<std::string>& default_wordlist()
{
    static const std::vector<std::string> words = {
        "www", "api", "mail", "dev", "test", "staging", "admin", "app",
        "portal", "vpn", "blog", "shop", "auth", "cdn", "static", "docs",
        "support", "status", "files", "ftp", "beta", "dashboard", "git", "m"
    };
    return words;
}
}

std::vector<SubdomainInfo> discover_subdomains(
    const std::string& hostname,
    const SubdomainOptions& options,
    SubdomainStats* outputStats)
{
    SubdomainStats localStats;
    SubdomainStats& stats = outputStats == nullptr ? localStats : *outputStats;
    stats = {};

    std::vector<std::string> rawWords = options.words;
    if (!options.wordlistPath.empty())
    {
        std::ifstream wordlist(options.wordlistPath);
        if (!wordlist)
        {
            stats.wordlistError = "Could not open wordlist: " + options.wordlistPath;
            return {};
        }

        std::string line;
        while (std::getline(wordlist, line))
        {
            const std::string cleaned = trim(line);
            if (!cleaned.empty() && cleaned.front() != '#' && cleaned.front() != ';')
            {
                rawWords.push_back(cleaned);
            }
        }
    }

    if (rawWords.empty())
    {
        rawWords = default_wordlist();
    }

    std::unordered_set<std::string> uniqueWords;
    std::vector<std::string> words;
    const std::size_t candidateLimit = options.maxCandidates == 0
        ? rawWords.size()
        : options.maxCandidates;

    for (std::string word : rawWords)
    {
        if (!normalize_label(word))
        {
            ++stats.invalidWords;
            continue;
        }

        if (uniqueWords.insert(word).second)
        {
            words.push_back(word);
            if (words.size() >= candidateLimit)
            {
                break;
            }
        }
    }

    stats.candidates = words.size();
    std::vector<SubdomainInfo> found;

    for (const std::string& word : words)
    {
        const std::string candidate = word + "." + hostname;
        ++stats.attempted;

        const DnsResult dns = resolve_dns_details(candidate);
        if (dns.status == DnsStatus::Resolved && !dns.addresses.empty())
        {
            found.push_back({candidate, dns.addresses, DnsStatus::Resolved});
        }
        else if (dns.status == DnsStatus::Timeout)
        {
            ++stats.timedOut;
            stats.stoppedOnTimeout = true;
            break;
        }
        else if (dns.status == DnsStatus::Error)
        {
            ++stats.errors;
        }
        else
        {
            ++stats.unresolved;
        }

        if (options.delayMs > 0 && stats.attempted < words.size())
        {
            std::this_thread::sleep_for(std::chrono::milliseconds(options.delayMs));
        }
    }

    return found;
}

std::vector<std::string> discover_subdomains(const std::string& hostname)
{
    const std::vector<SubdomainInfo> discovered = discover_subdomains(
        hostname,
        SubdomainOptions{}
    );

    std::vector<std::string> names;
    names.reserve(discovered.size());
    for (const SubdomainInfo& item : discovered)
    {
        names.push_back(item.hostname);
    }
    return names;
}