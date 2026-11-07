with open('backend/app/rag/entities.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '"sip limit", "sip amount", "sip installment", "minimum sip investment",'
replacement = '"sip limit", "sip amount", "minimum sip investment",'

if target in content:
    content = content.replace(target, replacement)
    with open('backend/app/rag/entities.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully!")
else:
    print("Target not found!")
