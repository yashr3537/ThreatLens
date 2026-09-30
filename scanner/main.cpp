#include <iostream>
#include "core/target.h"
#include "core/result.h"

int main()
{
    std::string input;

    std::cout << "Enter target: ";
    std::cin >> input;

    Target target = create_target(input);

    Result result;

    result.target = target.input;
    result.hostname = target.hostname;
    result.ip = target.ip;

    show_result(result);

    return 0;
}