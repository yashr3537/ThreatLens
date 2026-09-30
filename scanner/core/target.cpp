#include "target.h"

Target create_target(const std::string& input)
{
    Target target;

    target.input = input;
    target.hostname = input;
    target.ip = "";
    target.valid = !input.empty();

    return target;
}