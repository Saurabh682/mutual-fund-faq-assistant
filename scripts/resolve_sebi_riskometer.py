import urllib.request

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFsonO942q9HLspqa29euqCBqF3fm7JfbwfaQEzOnXu2cq6XQ-Mcy-ykTjV-WlF3kR1Z30fGK2SVqhCqrUoRtN6SoKZPTyGtkAmg5BnAMr3vvtX3fEExU3iXvhvGfIPUSNqCsWFnncVPOI7BRzEb7DUwBvF6Bv61ePcHhyDVrfqnCMmhJ6fBvg2jUY_NSbiSDn9uoeZ_n4LWZDtWM5T-VW01IIiSHY0Y7ElsXlLLexBMiCz"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        print("Resolved URL:", resp.geturl())
except Exception as e:
    print("Error:", e)
