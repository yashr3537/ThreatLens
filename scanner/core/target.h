#ifndef TARGET_H
#define TARGET_H

#include <string>

struct Target
{
    std::string input;
    std::string scheme;
    std::string hostname;
    std::string path;
    int port;
    bool valid;
};

Target create_target(const std::string& input);

#endif