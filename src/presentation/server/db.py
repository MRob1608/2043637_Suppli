import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host="rule-database",
        database="rules_db",
        user="mars_user",
        password="mars_password"
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    with open("schema.sql", "r") as f:
        cur.execute(f.read())

    conn.commit()
    cur.close()
    conn.close()
