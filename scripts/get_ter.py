import sqlite3
conn = sqlite3.connect('data/index/facts.db')
c = conn.cursor()
c.execute("SELECT scheme_id, field, value FROM facts WHERE field = 'ter_direct'")
for row in c.fetchall():
    print(row)
