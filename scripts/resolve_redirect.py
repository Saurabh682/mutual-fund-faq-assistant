import urllib.request

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEIOOul5EdvS2CaQVO8dIbyKGquSkESHaTFC9EHaMp4vuNFXhfwCubTeY5iGfThBZR7MCXDFMEGw-CLu9u3Wx7kYDf66MiP6dF-b4k68PghBz_lQftPh6hct_Z_yGNlGshTyTW1X4sRUuTzgBfDKXMsbi8rZtuqpo-3HcKZs9XSe7iSJT1mP6mY9a1MRPuZElqyqKwHDoSobyk="

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        print("Resolved URL:", resp.geturl())
except Exception as e:
    print("Error:", e)
