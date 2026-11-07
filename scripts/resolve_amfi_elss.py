import urllib.request

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHo97SiuVbq_MZPyVu-Gb125wo2_ybIdkGlFArZM9rw05vqOF92Qm23kEUGE2Syb2IXpifj71KN-I5Ij1vtIF42r7XKsfyxxd5QdPdh0EHVkC3Uo2qeCdQLRAqrZZBpnP8vATE="
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        print("Resolved:", resp.geturl())
except Exception as e:
    print("Error:", e)
