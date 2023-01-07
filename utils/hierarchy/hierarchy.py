import sqlite3

from db_instance import db
from utils.exceptions import *


class Hierarchy:
    def __init__(self):
        self.root = "Hierarchy"

    @staticmethod
    def add_node(value, parent=None):
        if not parent:
            try:
                db.query("INSERT INTO specialities VALUES(?, ?)", (None, value))
            except sqlite3.IntegrityError as ie:
                raise sqlite3.IntegrityError(f"Speciality *{value}* already exists") from ie
        else:
            result_parent = db.fetchone("SELECT * FROM specialities WHERE speciality = ?", (parent,))
            if not result_parent:
                raise ValueError(f"Parent speciality *{parent}* doesn't exists.")

            parent_id = result_parent[0]
            try:
                db.query("INSERT INTO users_groups VALUES(?, ?, ?)", (None, value, parent_id))
            except sqlite3.IntegrityError as ie:
                raise sqlite3.IntegrityError(f"Group *{value}* already exists.") from ie

    @staticmethod
    def edit_node(old_value, new_value, parent=None):
        if old_value == new_value:
            raise ValueError(f"*{old_value}* and *{new_value}* - two same values.")

        if not parent:
            was_added = db.query("UPDATE specialities SET speciality = ? WHERE speciality = ?",
                                 (new_value, old_value))
            if not was_added:
                raise ExistenceError(f"Speciality *{old_value}* doesn't exists.")
        else:
            parent_res = db.fetchone("SELECT * FROM specialities WHERE speciality = ?", (parent,))
            if not parent_res:
                raise ValueError(f"Parent speciality *{parent}* doesn't exists.")
            parent_id = parent_res[0]

            was_added = db.query("UPDATE users_groups SET user_group = ? WHERE user_group = ? AND parent_speciality = ?",
                                 (new_value, old_value, parent_id))

            if not was_added:
                raise ExistenceError(f"Group *{old_value}* doesn't exists.")

    @staticmethod
    def delete_node(value, parent=None):
        if not parent:
            was_deleted = db.query("DELETE FROM specialities WHERE speciality = ?", (value,))
            if not was_deleted:
                raise ExistenceError(f"Speciality {value} doesn't exists.")
        else:
            parent_res = db.fetchone("SELECT * FROM specialities WHERE speciality = ?", (parent,))
            if not parent_res:
                raise ValueError(f"Parent speciality *{parent}* doesn't exists.")
            parent_id = parent_res[0]

            was_deleted = db.query("DELETE FROM users_groups WHERE user_group = ? AND parent_speciality = ?", (value, parent_id))
            if not was_deleted:
                raise ExistenceError(f"Group *{value}* doesn't exists.")

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





