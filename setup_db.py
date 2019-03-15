import psycopg2
import sys
from dbconfig import dbconfig
params = dbconfig()
conn = psycopg2.connect(**params)
try:
    
    conn.autocommit = True
    command = "CREATE DATABASE fenceviolation;"
    cur = conn.cursor()
    cur.execute(command)
    cur.close()
except psycopg2.DatabaseError as e:
    print(e)
except Exception as e:
    print(e)
    sys.exit(1)
finally:
    conn.close()


def table_exists(c, tn):
    query = """SELECT EXISTS(SELECT relname FROM pg_class WHERE relname= '{}')""".format(
        tn)
    resp = c.execute(query)
    rows = c.fetchone()
    print(rows[0])
    return rows[0]



try:
    conn = psycopg2.connect(**params)
    conn.autocommit = True
    cur = conn.cursor()
    table_name = 'fence_violations'
    if not table_exists(cur, table_name):
        commands = [
            """CREATE TABLE {} (
            violation_id INTEGER PRIMARY KEY,
            frame_name text,
            status boolean DEFAULT FALSE,
            update_time BIGINT,
            violation_time BIGINT
        );""".format(table_name)
        ]
        for c in commands:
            cur.execute(c)
    cur.close()
finally:
    conn.close()
