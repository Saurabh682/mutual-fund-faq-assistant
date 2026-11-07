import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/index/facts.db')
c = conn.cursor()
c.execute("SELECT scheme_id, field, value, as_of, source_url FROM facts WHERE field = 'fund_manager'")
for row in c.fetchall():
    print(row)
