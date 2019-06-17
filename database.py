import sqlite3
import time
import random
class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY,
                frame_path TEXT,
                status boolean DEFAUL FALSE,
                created_time BIGINT
            )
            """)
        self.conn.commit()

    def select_all(self):
        self.cursor.execute("SELECT * FROM violations ;")
        rows = self.cursor.fetchall()
        return rows

    def select(self, id):
        self.cursor.execute("SELECT * FROM violations WHERE id = ? ;", id)
        row = self.cursor.fetchall()
        return row[0]

    def select_with_offset(self, offset):
        self.cursor.execute("SELECT * FROM violations LIMIT 100 OFFSET {} ;".format(offset))
        rows = self.cursor.fetchall()
        return rows

    def __del__(self):
        self.conn.close()

    def insert(self, frame_path):
        now = int(time.time())
        id  = now * 10000000 + random.randint(0, 10000)
        try:
            self.conn.execute("INSERT INTO violations VALUES(?, ?, ?, ?);", (id, frame_path, False, now))
            self.conn.commit()
        except:
            print("Faled to insert to Database")
            pass
        return (id, False, now)
    
    def update_status(self, id):
        try:
            self.conn.execute("UPDATE violations SET status = ? WHERE id = ? ;", (1, id))
            self.conn.commit()
        except:
            pass
        
    def delete_row(self, id):
        self.conn.execute("DELETE FROM violations WHERE id = ? ;", (id))
        self.conn.commit()

    def delete_all(self):
        self.conn.execute("DELETE FROM violations ;")
        self.conn.commit()

    