import re

for p in ['backend/tests/test_phase1.py', 'backend/tests/test_phase3.py']:
    print(f"=== {p} ===")
    with open(p, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        if 'fund_manager' in l:
            for j in range(max(0, i-2), min(len(lines), i+4)):
                print(f"{j+1:4d}: {lines[j].rstrip()}")
            print("-" * 40)
