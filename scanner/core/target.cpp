#include "target.h"

Target create_target(const std::string& input)
{
    Target target;

    target.input = input;
    target.scheme = "";
    target.hostname = "";
    target.path = "/";
    target.port = 0;
    target.valid = false;

    std::string url = input;

    // Scheme
    if (url.rfind("https://", 0) == 0)
    {
        target.scheme = "https";
        target.port = 443;
        url = url.substr(8);
    }
    else if (url.rfind("http://", 0) == 0)
    {
        target.scheme = "http";
        target.port = 80;
        url = url.substr(7);
    }
    else
    {
        return target;
    }

    // Hostname
    size_t slash = url.find('/');

    if (slash == std::string::npos)
    {
        target.hostname = url;
    }
    else
    {
        target.hostname = url.substr(0, slash);
        target.path = url.substr(slash);
    }

    target.valid = !target.hostname.empty();

    return target;
}