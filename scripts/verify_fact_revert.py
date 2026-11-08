import sys
sys.path.insert(0, "backend")

from app.rag.facts import lookup_fact

f = lookup_fact("Who is the fund manager of HDFC Mid Cap?")
print("Text:", f["text"])
print("Source URL:", f["citation_url"])
print("Last Updated:", f["last_updated"])
print("Groww scheme page present:", "Groww scheme page" in f["rendered"])
