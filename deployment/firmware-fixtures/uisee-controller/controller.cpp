// Synthetic controller for exercising the Workbench's compiled fixture path.
#include <charconv>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <string_view>
#include <system_error>

bool setValveTarget(double requested, double& target) {
    if (!std::isfinite(requested) || requested < 0 || requested > 100) {
        return false;
    }
    target = requested;
    return true;
}

int main() {
    double target = 0;
    std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
    for (std::string request; std::getline(std::cin, request);) {
        if (request.compare(0, 4, "SET ") == 0) {
            std::string_view value(request.data() + 4, request.size() - 4);
            double requested = 0;
            const char* end = value.data() + value.size();
            auto parsed = std::from_chars(value.data(), end, requested);
            if (parsed.ec != std::errc{} || parsed.ptr != end ||
                !setValveTarget(requested, target)) {
                std::cout << "ERROR\n" << std::flush;
                continue;
            }
        } else if (request != "READ") {
            std::cout << "ERROR\n" << std::flush;
            continue;
        }
        std::cout << "OK " << target << '\n' << std::flush;
    }
    return std::cin.eof() ? 0 : 1;
}
