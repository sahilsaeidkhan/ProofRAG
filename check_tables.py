from src.db import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT count(*) FROM chunks")
print("chunks:", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM faq_questions")
print("faq:", cur.fetchone()[0])
conn.close()