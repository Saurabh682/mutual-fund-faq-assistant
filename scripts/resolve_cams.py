import urllib.request

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF8P5CzByBZz-y8VMcruf0PFx1lltPKizD0-VQRBKHmwLsheSlvtevC5Iv82o_mbWpogGGDGzDLO6J0yTF_4xSPvgW2F-jRiy_x7MaYULqz5y4Tl9wss2aIcRAhrpEpD_PmEyixlDHqswxUbTEbzbtRDfs6bgeKY7_pwOuR4CXiUMgoZQ=="
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        print("Resolved URL:", resp.geturl())
except Exception as e:
    print("Error:", e)
