import urllib.request

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGW1PQIQdIcS9RtfndHaHPY5gM8eHVC-uyVkDKZbslqVemD8s4ZJOYx9mxmCFPrIUg2vgNxJirUOi6WqGCseIFLf8cCWR0s46rvAt98k5M3zTdzAGJS2yjaTchRLZCP0aGuGrz351LBBpddDRw_5sxDXXt0Z0dz2tmFIaSHy_KGw-sC14Ksfq84qir1NR7h82GRVmyHxTzP2Be2L0pJIxRy_jTADPGxb_eCHdfvCUCA96qEa9i30wn4pYpWBQ=="
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        print("Resolved URL:", resp.geturl())
except Exception as e:
    print("Error:", e)
