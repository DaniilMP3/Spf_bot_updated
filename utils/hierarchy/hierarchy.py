from db_instance import db


class Hierarchy:
    def __init__(self):
        self.root = "Hierarchy"

    @staticmethod
    def add_node(value, parent=None):
        if not parent:
            if not db.in_database("specialities", "speciality", value):
                db.query("INSERT INTO specialities VALUES(?, ?)", (None, value))
            else:
                return False
        else:
            result_parent = db.fetchone("SELECT * FROM specialities WHERE speciality = ?", (parent,))
            if not result_parent:
                return False

            parent_id = result_parent[0]
            result_group = db.fetchone("SELECT * FROM users_groups WHERE user_group = ? AND parent_speciality = ?", (value, parent_id))
            if result_group:
                return False
            else:
                db.query("INSERT INTO users_groups VALUES(?, ?, ?)", (None, value, parent_id))

        return True

    @staticmethod
    def edit_node(old_value, new_value, parent=None):
        if not parent:
            if not db.in_database("specialities", "speciality", old_value):
                return False
            else:
                db.query("UPDATE specialities SET speciality = ? WHERE speciality = ?", (new_value, old_value))
        else:
            if db.in_database("users_groups", "user_group", new_value):
                return False
            elif db.query("UPDATE users_groups SET user_group = ? WHERE user_group = ?", (new_value, old_value)):
                return True

    @staticmethod
    def delete_node(value, parent=None):
        if not parent:
            if not db.in_database("specialities", "speciality", value):
                return False
            else:
                db.query("DELETE FROM specialities WHERE speciality = ?", (value,))
                return True
        else:
            result_parent = db.fetchone("SELECT * FROM specialities WHERE speciality = ?", (parent,))
            parent_id = result_parent[0]

            if not result_parent:
                return False

            elif db.query("DELETE FROM users_groups WHERE user_group = ? AND parent_speciality = ?", (value, parent_id)):
                return True

    @staticmethod
    def delete_all():
        if any([db.query("DELETE FROM specialities"), db.query("DELETE from users_groups")]):
            return True
        return False

    def __str__(self):
        res = ""
        roots = list(db.fetchall("SELECT * FROM specialities"))
        for r in roots:
            speciality_name = r[1]
            parent_id = r[0]

            res += speciality_name + '\n'
            children = list(db.fetchall("SELECT * FROM users_groups WHERE parent_speciality = ?", (parent_id,)))
            for c in children:
                children_name = c[1]
                res += '\t' + '·' + children_name + '\n'

        return res





