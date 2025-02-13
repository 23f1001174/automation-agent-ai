import requests
from bs4 import BeautifulSoup

URL = "https://pypi.org/simple/"

def fetch_packages(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        packages = [a.text.strip() for a in soup.find_all('a')]
        
        with open("packages.txt", "w", encoding="utf-8") as file:
            for pkg in packages:
                file.write(pkg + "\n")  # Write each package on a new line

        print(f"Successfully saved {len(packages)} packages to packages.txt")
    else:
        print("Error fetching packages!")

fetch_packages(URL)
