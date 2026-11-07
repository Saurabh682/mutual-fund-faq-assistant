with open("backend/tests/test_static_contract.py", "r", encoding="utf-8") as f:
    tsc = f.read()

tsc = tsc.replace(
    '            "What is mutual fund settlement cycle for redemptions?",\n        ]',
    '            "What is mutual fund settlement cycle for redemptions?",\n            "How do I download my Capital Gains statement on Groww?",\n        ]'
)
tsc = tsc.replace(
    '        unsupported_queries = [\n            "How do I download my Capital Gains statement on Groww?",',
    '        unsupported_queries = ['
)

with open("backend/tests/test_static_contract.py", "w", encoding="utf-8") as f:
    f.write(tsc)

with open("backend/tests/test_intent.py", "r", encoding="utf-8") as f:
    ti = f.read()

ti = ti.replace(
    '("How do I download my Capital Gains statement on Groww?", False),',
    '("How do I download my Capital Gains statement on Groww?", True),'
)
ti = ti.replace(
    '("how to download capital gains statement", False),',
    '("how to download capital gains statement", True),'
)
ti = ti.replace(
    '("Where can I find my capital gains report on Groww?", False),',
    '("Where can I find my capital gains report on Groww?", True),'
)

with open("backend/tests/test_intent.py", "w", encoding="utf-8") as f:
    f.write(ti)

print("Updated tests for capital gains")
