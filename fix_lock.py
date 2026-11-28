from src.db import get_connection

conn = get_connection()
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
    SELECT pid, state FROM pg_stat_activity
    WHERE datname = 'proofrag' AND pid <> pg_backend_pid()
""")
rows = cur.fetchall()
print("dusre sessions:", rows)
for pid, state in rows:
    cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
    print("band kiya:", pid, cur.fetchone())
conn.close()