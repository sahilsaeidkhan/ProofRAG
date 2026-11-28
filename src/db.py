import os

from dotenv import load_dotenv
import psycopg

load_dotenv()

DB_HOST = "proofrag-db.c1eq4wmi0tw8.ap-south-1.rds.amazonaws.com"
DB_NAME = "proofrag"
DB_USER = "proofrag_admin"


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=os.environ["DB_PASSWORD"],
        sslmode="require",
    )