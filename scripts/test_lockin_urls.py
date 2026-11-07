import urllib.request

urls = [
    "https://groww.in/p/lock-in-period",
    "https://groww.in/blog/lock-in-period-in-mutual-funds",
    "https://groww.in/p/elss-mutual-funds",
]

headers = {'User-Agent': 'Mozilla/5.0'}
for u in urls:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"OK {resp.status}: {u} ({len(resp.read())} bytes)")
    except Exception as e:
        print(f"Failed {u}: {e}")
