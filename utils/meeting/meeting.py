import random

from db_instance import db
import datetime
from redis import Redis, StrictRedis
from utils.exceptions import *

PRIORITIES = {"0": {"sex": False, "course": True, "speciality": True, "user_group": False},
              "1": {"sex": False, "course": True, "speciality": False, "user_group": False},
              "2": {"sex": False, "course": True, "speciality": True, "user_group": True},
              "3": {"sex": False, "course": False, "speciality": True, "user_group": False},
              "4": {"sex": False, "course": False, "speciality": False, "user_group": False}}


class MeetingsManager:

    def __init__(self, red):
        if not any([isinstance(red, Redis), isinstance(red, StrictRedis)]):
            raise TypeError("Redis instance should be Redis or StrictRedis")
        self.red = red

    def queueAppend(self, value):
        self.red.rpush("queue", value)

    def queuePop(self):
        return self.red.rpop("queue")

    @staticmethod
    def get_userInfo(user_id):
        user_res = db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user_res:
            raise ExistenceError(f"User {user_id} not exists.")

        user_groupId = user_res[5]
        group_res = db.fetchone("SELECT * FROM users_groups WHERE id = ?", (user_groupId,))

        specialityId = group_res[2]
        speciality_res = db.fetchone("SELECT * FROM specialities WHERE id = ?", (specialityId,))

        user_sex, user_course, user_speciality, user_group = user_res[3], user_res[4], speciality_res[1], group_res[1]
        return [user_sex, user_course, user_speciality, user_group]

    @staticmethod
    def isMatch(priority, **kwargs: bool):
        priorities_table = PRIORITIES[str(priority)]
        userData_table = kwargs

        priorities_keys = set(priorities_table.keys())
        userData_keys = set(userData_table.keys())
        if priorities_keys != userData_keys:
            raise KeyError("Current keys are not available.")

        shared_items = {k: priorities_table[k] for k in priorities_table if k in userData_table and priorities_table[k] == userData_table[k]}
        print(shared_items)

        if len(shared_items) != len(priorities_table):
            return False

        return True

    async def get_partner(self, user_id):
        user_sex1, user_course1, user_speciality1, user_group1 = self.get_userInfo(user_id)

        queue_bytes = self.red.lrange('queue', 0, -1)

        queue = [x.decode("utf-8") for x in queue_bytes]

        best_candidates = []
        x = 0
        priorities_number = len(PRIORITIES)

        was_found = False
        while x != priorities_number:
            for i, v in enumerate(queue):
                user_sex2, user_course2, user_speciality2, user_group2 = self.get_userInfo(v)
                if self.isMatch(x, sex=user_sex1 == user_sex2,
                                speciality=user_speciality1 == user_speciality2,
                                course=user_course1 == user_course2,
                                user_group=user_group1 == user_group2):

                    best_candidates.append(v)
                    del queue[i]
                    was_found = True

            if was_found:
                break

            x += 1

        if not was_found:
            self.queueAppend(user_id)
            return False

        candidate_id = random.choice(best_candidates)
        return candidate_id








