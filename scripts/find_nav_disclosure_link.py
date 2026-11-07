import urllib.request
from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

soup = BeautifulSoup(html, 'html.parser')
for tag in soup.find_all(text=re.compile(r"Disclosure of NAV")):
    parent = tag.parent
    print("Tag:", tag)
    print("Parent:", parent)
    if parent.name == 'a':
        print("Href:", parent.get('href'))
    elif parent.find('a'):
        print("Child href:", parent.find('a').get('href'))
