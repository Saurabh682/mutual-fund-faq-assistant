import urllib.request

urls = [
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEJt7h80f_ez4TU0CKq2cBLqy4ZccI7_64ROp7OvPhewMyA1wvYz8gCvB0NIKC7q_wQKydVsjxHGlCx50rpDeFrfImBBiEoFGeayVpeBHqfdf99fLh8MBCysbU04hXmfZUfuClB_wZl2DehE-zKr-gcjDCDZQLA4siGD2rXvTGZzsKmSUWKG26pmkIbaT8fm8T36w==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF-KeohTvRhqqxRYE5233guMB9k8INy19_B_wyMiTQpTrerCu9TKrMvOCSX4TFz2nqQyg-1_oBgXQ53iXpCpcowJFunjUefPfMTlSd6x18IovU5kbZedn8-efAXjncyQoUFekiOc7IlUnkgMU1nl2ckSdH2Ig==",
]

headers = {'User-Agent': 'Mozilla/5.0'}
for u in urls:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            print("Resolved:", resp.geturl())
    except Exception as e:
        print("Error:", e)
