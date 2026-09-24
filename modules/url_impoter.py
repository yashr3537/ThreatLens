def single_url():
    # FIX: invalid input ke baad dobara input lene ke liye loop chahiye
    while True:
        urls = input("Enter url: ")

        if urls == "":
            print("url can't be empty")
            continue

        elif not urls.startswith("http://") and not urls.startswith("https://"):
            print("url should start with http:// or https://")
            continue

        else:
            print("url is valid")
            return urls


def multiple_urls():
    print("enter urls 1:")
    print("import file 2:")

    chosen = input("choose 1 or 2: ")

    if chosen == "1":

        url_input = input("Enter urls separated by commas: ")
        urls = url_input.split(",")

        # FIX: valid URLs ko alag list me collect karenge
        valid_urls = []

        for url in urls:
            url = url.strip()  # FIX: comma ke baad ke spaces remove

            if url == "":
                print("url can't be empty")
                continue

            elif not url.startswith("http://") and not url.startswith("https://"):
                print("url should start with http:// or https://")
                continue

            else:
                print("url is valid")
                valid_urls.append(url)

        # FIX: loop complete hone ke baad return
        return valid_urls

    elif chosen == "2":

        file_path = input("Enter file path: ")

        try:
            with open(file_path, "r") as f:
                urls = f.read().splitlines()

            # FIX: sirf valid URLs collect karenge
            valid_urls = []

            for url in urls:
                url = url.strip()

                if url == "":
                    print("url can't be empty")
                    continue

                elif not url.startswith("http://") and not url.startswith("https://"):
                    print("url should start with http:// or https://")
                    continue

                else:
                    print("url is valid")
                    valid_urls.append(url)

            # FIX: saare URLs check hone ke baad return
            return valid_urls

        except FileNotFoundError:
            print("File not found. Please check the file path and try again.")
            return []  # FIX: None ke bajay empty list

    else:
        print("invalid choice")
        return []