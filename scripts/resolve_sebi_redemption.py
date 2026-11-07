import urllib.request

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHTGTjwtezx4KALnmbU-_hPQBbOggwdE2fmABBaSbqqcf_-X2PK2elBuEBEr5-obnTEgalMLps6zRDcqFRNQP6SmJHlmsQVDWoJnq08tEB87c-IwIXdKo0Fn4ln_NObCzjC8pwPTDWUlWxKs4s9ORtI6Ik2NotbZn2neqrnZRqPpUg="
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        print("Resolved URL:", resp.geturl())
except Exception as e:
    print("Error:", e)
