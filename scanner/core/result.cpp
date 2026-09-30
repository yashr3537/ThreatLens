#include "result.h"
#include <iostream>

void show_result(const Result& result)
{
    std::cout << "\n========== THREATLENS RESULT ==========\n";

    std::cout << "Target   : " << result.target << "\n";
    std::cout << "Hostname : " << result.hostname << "\n";
    std::cout << "IP       : " << result.ip << "\n";

    std::cout << "Subdomains: " << result.subdomains.size() << "\n";
    std::cout << "Ports     : " << result.ports.size() << "\n";

    std::cout << "========================================\n";
}