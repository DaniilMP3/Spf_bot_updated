import sqlite3


class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys = on")
        self.connection.commit()

        self.cursor = self.connection.cursor()

    def create_tables(self):
        """
        https://imgur.com/a/wenCbOz
        """

        self.cursor.execute("CREATE TABLE IF NOT EXISTS specialities("
                            "id INT PRIMARY KEY,"
                            "speciality VARCHAR)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS users_groups("
                            "id INT PRIMARY KEY,"
                            "user_group VARCHAR,"
                            "parent_speciality INTEGER,"
                            "FOREIGN KEY(parent_speciality) REFERENCES specialities(id) ON DELETE CASCADE)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS users("
                            "id INTEGER PRIMARY KEY,"
                            "user_id INTEGER NOT NULL,"
                            "full_name VARCHAR NOT NULL,"
                            "sex VARCHAR NOT NULL,"
                            "course INTEGER,"
                            "user_group INTEGER,"
                            "meetings_count INTEGER, "
                            "FOREIGN KEY(user_group) REFERENCES users_groups(id) ON DELETE CASCADE)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS links("
                            "id INTEGER PRIMARY KEY,"
                            "link VARCHAR NOT NULL)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS meetings("
                            "id INTEGER PRIMARY KEY,"
                            "first_user INTEGER,"
                            "second_user INTEGER,"
                            "link INTEGER,"
                            "FOREIGN KEY(link) REFERENCES links(id),"
                            "FOREIGN KEY(first_user) REFERENCES users(id),"
                            "FOREIGN KEY(second_user) REFERENCES users(id) ON DELETE CASCADE)")

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

    async def query(self, query, args=None):
        if args:
            self.cursor.execute(query, args)
        else:
            self.cursor.execute(query)

        self.connection.commit()
