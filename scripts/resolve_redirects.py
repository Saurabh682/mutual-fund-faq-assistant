import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHaRIXgI0sc1r0lt2trMZNPmOUpoyF7nvu-AI2u_7PGe3PCWDS_4HU1vm9mE0hHHO8sqwMWaAIcTiV37pvKmqiBjMHGs5CM_RKC0aOzA3LEUta-rYj0rVxZxUwl1t47GWd3sMmYCFU6lUOia15MWV0UE956kCxyIlLtMHm-0Pc2Pd1ELNKAcUyYxdhG4Zs_VvdylLl4BfWlIXEO",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGwDXuactJxDIzCLKGybgjZn2QrVRYah9R0uslq5ZolfuBzVSyGYFmttAyOJfKKa24pS0I2mofVMgd66YMd9ciPiBMkhqTznyzo5suKEKAaxRLwbEnoXFbOD4VUAI34ty4yZfrkHvztNQyu--0zI9Vpcl2xU4hfeu4D3_VusZ0mvxXwUljobu7XZG2FBRtseLWgew==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGgPeBGbmQePhopJpkQWI5kbuZaEfstPTdCFf_xjvm4J5VjPliFr1zCMTLtkqy8WDCJk-2snnw0I9yzMYBIcKf9QASeEhAoccqWdhM7VDt0KbhOBSQNqMf0FfwveLfG4Lc4Bph8mS02SnwfE7EAATt5FjsZPzAw8p9Uc4l_53UEuK4XC8NDugroTAk="
]

headers = {"User-Agent": "Mozilla/5.0"}
for u in urls:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print("Resolved URL:", resp.geturl())
    except Exception as e:
        print("Error:", e)
