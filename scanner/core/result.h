#ifndef RESULT_H
#define RESULT_H

#include <string>
#include <vector>

struct Result
{
    std::string target;
    std::string hostname;
    std::string ip;

    std::vector<std::string> subdomains;
    std::vector<std::string> ports;
};

void show_result(const Result& result);

#endif