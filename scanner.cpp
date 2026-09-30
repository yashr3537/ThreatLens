#include <iostream>
#include <string>
#include <curl/curl.h>


// ==================================================
// RESPONSE DATA KO HANDLE KARNE KA FUNCTION
// ==================================================

size_t write_data(
    void* contents,
    size_t size,
    size_t nmemb,
    void* userp
) {

    // Response body ko abhi store nahi karna hai.
    // Sirf response check karna hai.
    return size * nmemb;
}


// ==================================================
// MAIN SCAN FUNCTION
// ==================================================

void scan_target(std::string target) {

    // URL ke aage-peeche ki extra spaces hatao.
    while (!target.empty() &&
           (target.back() == ' ' || target.back() == '\n' || target.back() == '\r')) {
        target.pop_back();
    }

    while (!target.empty() && target.front() == ' ') {
        target.erase(target.begin());
    }


    // ==================================================
    // URL / IP CHECK
    // ==================================================

    // Agar user ne http:// ya https:// nahi diya
    // to default HTTP use karenge.
    //
    // Isse ye bhi support honge:
    //
    // example.com
    // 192.168.1.1
    // localhost
    // 127.0.0.1

    if (
        target.find("http://") != 0 &&
        target.find("https://") != 0
    ) {

        target = "http://" + target;
    }


    // ==================================================
    // CURL INITIALIZE
    // ==================================================

    CURL* curl = curl_easy_init();

    if (!curl) {

        std::cout
            << "{\"status\":\"error\","
            << "\"error\":\"CURL initialization failed\"}";

        return;
    }


    // ==================================================
    // REQUEST SETTINGS
    // ==================================================

    curl_easy_setopt(
        curl,
        CURLOPT_URL,
        target.c_str()
    );


    // Response body ko ignore karo.
    curl_easy_setopt(
        curl,
        CURLOPT_WRITEFUNCTION,
        write_data
    );


    // Maximum wait time.
    curl_easy_setopt(
        curl,
        CURLOPT_TIMEOUT,
        8L
    );


    // Redirect follow karo.
    curl_easy_setopt(
        curl,
        CURLOPT_FOLLOWLOCATION,
        1L
    );


    // Maximum redirects.
    curl_easy_setopt(
        curl,
        CURLOPT_MAXREDIRS,
        5L
    );


    // ==================================================
    // REQUEST START
    // ==================================================

    CURLcode result = curl_easy_perform(curl);


    // ==================================================
    // CONNECTION ERROR
    // ==================================================

    if (result != CURLE_OK) {

        std::cout
            << "{\"status\":\"error\","
            << "\"error\":\""
            << curl_easy_strerror(result)
            << "\"}";

        curl_easy_cleanup(curl);

        return;
    }


    // ==================================================
    // STATUS CODE
    // ==================================================

    long status_code = 0;

    curl_easy_getinfo(
        curl,
        CURLINFO_RESPONSE_CODE,
        &status_code
    );


    // ==================================================
    // RESOLVED IP
    // ==================================================

    char* ip_address = nullptr;

    curl_easy_getinfo(
        curl,
        CURLINFO_PRIMARY_IP,
        &ip_address
    );


    // Agar IP nahi mila to unknown.
    std::string ip = "unknown";

    if (ip_address != nullptr) {
        ip = ip_address;
    }


    // ==================================================
    // SUCCESS RESULT
    // ==================================================

    std::cout
        << "{\"status\":\"success\","
        << "\"status_code\":"
        << status_code
        << ",\"ip\":\""
        << ip
        << "\"}";


    // ==================================================
    // CLEANUP
    // ==================================================

    curl_easy_cleanup(curl);
}


// ==================================================
// MAIN
// ==================================================

int main() {

    // Python se target receive karo.
    std::string target;

    std::getline(
        std::cin,
        target
    );


    // Empty input check.
    if (target.empty()) {

        std::cout
            << "{\"status\":\"error\","
            << "\"error\":\"Target is empty\"}";

        return 0;
    }


    // Actual scanning function call.
    scan_target(target);


    return 0;
}