def add_url(url):
    print("add  url's ")
    print("exit to type down")
    while True:
        url_input = input("Enter url: ")
        if url_input == "down":
            break
        elif url_input == "":
            print("url can't be empty")
            continue
        elif url_input in url:
            print("url already added")
            continue
        elif not url_input.startswith("http://") and not url_input.startswith("https://"):
            print("url should start with http:// or https://")
            continue

        else:
            url.append(url_input)
    add_url_file(url)


# url added to list and saved to file##################################################
def add_url_file(url):
    print("save existing file or create new file"+"\n"+"1. save existing file"+"\n"+"2. create new file")
    while True:   
        choice = input("enter choice: ")  

        if choice == "1":
            file_path_name = input("file name :")
            try:
                with open(file_path_name, 'a') as file:
                    for item in url:
                        file.write(item+"\n")
                print("url's added to existing file")
                break
            except PermissionError:
                print("path is not accessible or permission denied")

            except FileNotFoundError:
                print("file not found")

            except OSError:  
                print("any other error for writing file")
                
        elif choice == "2":
            print("enter new file name ")
            file_path_name = input("file name :")
            try:
                with open(file_path_name, 'w') as file:
                    for item in url:
                        file.write(item+"\n")
                    print("file created and url's added")
                break
            except PermissionError:
                print("path is not accessible or permission denied")
            except OSError:
                print("any other error for writing file")
        else:
            print("invalid choice")

#search url in file ###########################################################
def search_url():
    print("search url's enter file path")
    file_path = input("file path :")
    url_search = input("enter url to search :")
    try:
        with open(file_path, 'r') as file:
            urls = file.readlines()
            for url in urls:
                if url.strip() == url_search:
                    print("url found")
                    return
    except FileNotFoundError:
        print("file not found")
    except PermissionError:
        print("path is not accessible or permission denied")

# main funtion ################################################
url = []
while True:
    print("1. add url+\n2. search url+\n3. exit")
    choice = input("enter choice: ")
    if choice == "1":
        add_url(url)
    elif choice == "2":
        search_url()
    elif choice == "3":
        exit()
    else:
        print("invalid choice")
