import os

from dotenv import load_dotenv
import psycopg

load_dotenv()

conn = psycopg.connect(
    host="proofrag-db.c1eq4wmi0tw8.ap-south-1.rds.amazonaws.com",
    dbname="proofrag",
    user="proofrag_admin",
    password=os.environ["DB_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
conn.commit()
cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
print(cur.fetchone())
conn.close()