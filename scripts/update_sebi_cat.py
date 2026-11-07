with open('backend/app/rag/procedures.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        "narrative": (
            "SEBI categorizes equity mutual funds strictly by market capitalization: Large Cap (top 100 stocks), Mid Cap (101st to 250th), and Small Cap (251st onwards). "
            "Multi Cap schemes must maintain at least 25% allocation in each of Large Cap, Mid Cap, and Small Cap segments at all times."
        ),
        "table_rows": [
            ("Framework", "SEBI Scheme Categorization & Rationalization"),
            ("Large Cap Mandate", "Top 100 companies by market cap (min 80% allocation)"),
            ("Mid Cap Mandate", "101st to 250th companies (min 65% allocation)"),
            ("Small Cap Mandate", "251st company onwards (min 65% allocation)"),
        ],'''

replacement = '''        "narrative": (
            "Under SEBI Circular SEBI/HO/IMD/DF3/CIR/P/2017/114, mutual funds are classified into 5 primary groups: Equity, Debt, Hybrid, Solution Oriented, and Other Schemes. "
            "The 10 equity subcategories include Multi Cap, Large Cap (top 100 companies), Mid Cap (101st-250th), Small Cap (251st onwards), and ELSS."
        ),
        "table_rows": [
            ("Regulatory Framework", "SEBI Scheme Categorization (Oct 2017 Circular)"),
            ("Primary Scheme Groups", "Equity, Debt, Hybrid, Solution Oriented, and Other Schemes"),
            ("Key Equity Categories", "Multi Cap, Large Cap, Mid Cap, Small Cap, Large & Mid Cap, ELSS"),
            ("Market Cap Definitions", "Large: 1-100; Mid: 101-250; Small: 251st company onwards"),
        ],'''

assert target in content, "Target not found in procedures.py"
content = content.replace(target, replacement)
with open('backend/app/rag/procedures.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated sebi_categorization successfully!")
