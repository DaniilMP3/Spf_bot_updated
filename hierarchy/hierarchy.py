from create_bot import db


class Hierarchy:
    @staticmethod
    async def update_root(old_value: str, new_value: str):
        if await db.in_database("specialities", "speciality", old_value):
            await db.query("UPDATE specialities SET = ? WHERE speciality = ?", (new_value, old_value))
            return True
        return False

    @staticmethod
    async def create_root(value: str):
        if not await db.in_database("specialities", "speciality", value):
            await db.query("INSERT INTO specialities VALUES(?, ?)", (None, value))
            return True
        return False

