import sqlite3


class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users"
                            "id INT PRIMARY KEY,"
                            "user_id INT,"
                            "full_name VARCHAR,"
                            "sex VARCHAR,"
                            "speciality VARCHAR,"
                            "course VARCHAR,"
                            "group VARCHAR,"
                            "meetings_count INT")

    async def fetchone(self, query, args=None):
        if args:
            res = self.cursor.execute(query, args)
        else:
            res = self.cursor.execute(query)
        return res.fetchone()

    async def fetchall(self, query, args=None):
        if args:
            res = self.cursor.execute(query, args)
        else:
            res = self.cursor.execute(query)
        return res.fetchall()

    async def fetchmany(self, query, size, args=None):
        if args:
            res = self.cursor.execute(query, args)
        else:
            res = self.cursor.execute(query)
        return res.fetchmany(size)

