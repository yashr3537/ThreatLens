def add_url(url):
    print("add  url's ")
    print("exit to type down")
    while True:
        url_input = input("Enter url: ")
        if url_input == "down":
            break
        else:
            url.append(url_input)
    add_url_file(url)


 # url added to list and saved to file
def add_url_file(url):
    print("save existing file or create new file"+"\n"+"1. save existing file"+"\n"+"2. create new file")
    while True:   
        choice = input("enter choice: ")  
        if choice == "1":
            file_path_name = input("file name :")
            with open(file_path_name, 'a') as file:
                for item in url:
                    file.write("\n"+item)
            print("url's added to existing file")
            break
        elif choice == "2":
            print("enter new file name ")
            file_path_name = input("file name :")
            with open(file_path_name, 'w') as file:
                for item in url:
                    file.write("\n"+item)
                print("file created and url's added")
            break
        else:
            print("invalid choice"


def search_url():
    print("search url's enter file path")
    file_path = input("file path :")
    url_search = input("enter url to search :")
    with open(file_path, 'r') as file:
        urls = file.readlines()
        for url in urls:
            if url.strip() == url_search:
                print("url found")
                return
        print("url not found")

# main funtion
while True:
    url = []
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
