from modules.url_impoter import single_url,multiple_urls

from modules.url_chaker import check_urls

print("welcome")

print("single url 1:")
print("multiple urls 2:")

chosen = input("choose 1 or 2: ")

if chosen == "1":
    urls = single_url()

elif chosen == "2":
    urls = multiple_urls()

else:
    print("invalid choice")
    exit()

print("scanning urls...")

check_urls(urls)