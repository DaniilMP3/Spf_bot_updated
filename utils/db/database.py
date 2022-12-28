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
                            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                            "speciality VARCHAR)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS users_groups("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                            "user_group VARCHAR,"
                            "parent_speciality INTEGER,"
                            "FOREIGN KEY(parent_speciality) REFERENCES specialities(id) ON DELETE CASCADE)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS users("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                            "user_id INTEGER NOT NULL,"
                            "full_name VARCHAR NOT NULL,"
                            "sex VARCHAR NOT NULL,"
                            "course INTEGER,"
                            "user_group INTEGER,"
                            "meetings_count INTEGER, "
                            "FOREIGN KEY(user_group) REFERENCES users_groups(id) ON DELETE CASCADE)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS links("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                            "link VARCHAR NOT NULL)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS meetings("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                            "first_user INTEGER,"
                            "second_user INTEGER,"
                            "link INTEGER,"
                            "FOREIGN KEY(link) REFERENCES links(id),"
                            "FOREIGN KEY(first_user) REFERENCES users(id),"
                            "FOREIGN KEY(second_user) REFERENCES users(id) ON DELETE CASCADE)")

    def fetchone(self, query, args=None):
        if args:
            self.cursor.execute(query, args)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchone()

    def fetchall(self, query, args=None):
        if args:
            self.cursor.execute(query, args)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    def fetchmany(self, query, size, args=None):
        if args:
            self.cursor.execute(query, args)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchmany(size)

    def query(self, query, args=None):
        if args:
            self.cursor.execute(query, args)
        else:
            self.cursor.execute(query)

        self.connection.commit()

    def in_database(self, table, column, value):
        self.cursor.execute(f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {column} = {value})")
        if self.cursor.fetchone():
            return True

        return False
