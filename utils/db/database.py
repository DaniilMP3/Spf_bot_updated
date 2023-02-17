import sqlite3


class Database:
    def __init__(self, path):
        self._connection = sqlite3.connect(path)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.commit()

        self._cursor = self._connection.cursor()

    def create_tables(self):
        """
        https://imgur.com/a/wenCbOz
        """

        self._cursor.execute("CREATE TABLE IF NOT EXISTS specialities("
                             "id INTEGER PRIMARY KEY NOT NULL,"
                             "speciality VARCHAR UNIQUE COLLATE NOCASE)")

        self._cursor.execute("CREATE TABLE IF NOT EXISTS admins("
                             "id INTEGER PRIMARY KEY NOT NULL,"
                             "telegram_id INTEGER NOT NULL UNIQUE,"
                             "is_super_user INTEGER NOT NULL DEFAULT 0 CHECK(is_super_user IN (0,1)))"
                             )

        self._cursor.execute("CREATE TABLE IF NOT EXISTS users_groups("
                             "id INTEGER PRIMARY KEY NOT NULL,"
                             "user_group VARCHAR,"
                             "parent_speciality INTEGER,"
                             "FOREIGN KEY(parent_speciality) REFERENCES specialities(id) ON DELETE CASCADE,"
                             "UNIQUE(user_group COLLATE NOCASE, parent_speciality))")

        self._cursor.execute("CREATE TABLE IF NOT EXISTS users("
                             "id INTEGER PRIMARY KEY NOT NULL,"
                             "telegram_id INTEGER NOT NULL,"
                             "full_name VARCHAR NOT NULL,"
                             "sex VARCHAR NOT NULL,"
                             "course INTEGER,"
                             "user_group INTEGER,"
                             "meetings_count INTEGER, "
                             "FOREIGN KEY(user_group) REFERENCES users_groups(id) ON DELETE CASCADE)")

        self._cursor.execute("CREATE TABLE IF NOT EXISTS meetings("
                             "id INTEGER PRIMARY KEY NOT NULL,"
                             "first_user INTEGER,"
                             "second_user INTEGER,"
                             "first_link TEXT,"
                             "second_link TEXT,"
                             "time VARCHAR,"
                             "FOREIGN KEY(first_user) REFERENCES users(id) ON DELETE CASCADE,"
                             "FOREIGN KEY(second_user) REFERENCES users(id) ON DELETE CASCADE)"
                             )

    def fetchone(self, query, args=None):
        if args:
            self._cursor.execute(query, args)
        else:
            self._cursor.execute(query)
        return self._cursor.fetchone()

    def fetchall(self, query, args=None):
        if args:
            self._cursor.execute(query, args)
        else:
            self._cursor.execute(query)
        return self._cursor.fetchall()

    def fetchmany(self, query, size, args=None):
        if args:
            self._cursor.execute(query, args)
        else:
            self._cursor.execute(query)
        return self._cursor.fetchmany(size)

    def query(self, query, args=None):
        if args:
            self._cursor.execute(query, args)
        else:
            self._cursor.execute(query)

        if self._cursor.rowcount == 1:

            self._connection.commit()
            return True
        return False

    def in_database(self, table, column, value):
        self._cursor.execute(f"SELECT 1 FROM {table} WHERE {column} = ?", (value,))
        if self._cursor.fetchone():
            return True

        return False
