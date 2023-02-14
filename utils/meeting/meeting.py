import json
import ast

import redis

from db_instance import db
from datetime import date, timedelta
import datetime
import time
import uuid
from redis import Redis, StrictRedis
from cfg import *
import jwt
from utils.exceptions import *
from utils.data_classes import *
from typing import Union, Any
import pickle


_PRIORITIES = {"0": {"sex": False, "course": True, "speciality": True, "user_group": False},
               "1": {"sex": False, "course": True, "speciality": False, "user_group": False},
               "2": {"sex": False, "course": True, "speciality": True, "user_group": True},
               "3": {"sex": False, "course": False, "speciality": True, "user_group": False},
               "4": {"sex": False, "course": False, "speciality": False, "user_group": False}}


class MeetingsManager:

    def __init__(self, red: Union[Redis, StrictRedis]):
        self.__red = red

    def hget(self, name: str, key: str):
        return pickle.loads(self.__red.hget(name, key))

    def hset(self, name: str, key: str, value: Union[bytes, memoryview, str, int, float, dict, list]):
        return self.__red.hset(name, key, pickle.dumps(value))

    def hdel(self, name: str, key: str):
        return self.__red.hdel(name, key)

    def lrange(self, key: str, from_point: int, to_point: int):
        return self.__red.lrange(key, from_point, to_point)

    def list_append(self, key: str, value: Union[QueueUser, bytes, memoryview, str, int, float]):
        if isinstance(value, QueueUser):
            user_id, inQueue_since = value
            dic = {"user_id": user_id, "time_inQueue": inQueue_since}
            dic_dumps = json.dumps(dic)
            self.__red.rpush(key, dic_dumps)
        else:
            self.__red.rpush(key, value)

    def list_lrem(self, key: str, count: int, value: Union[QueueUser, bytes, memoryview, str, int, float]):
        if isinstance(value, QueueUser):
            user_id, inQueue_since = value
            dic = {"user_id": user_id, "time_inQueue": inQueue_since}
            dic_dumps = json.dumps(dic)
            self.__red.lrem(key, count, dic_dumps)
        else:
            self.__red.lrem(key, count, value)

    def value_exists_in_list(self, key: str, value: Union[bytes, memoryview, str, int, float]):
        if self.__red.lrem(key, 0, value):
            self.list_append(key, value)
            return 1
        return 0

    @staticmethod
    def get_userInfo(user_id: int) -> User:
        user_res = db.fetchone("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
        if not user_res:
            raise ExistenceError(f"User {user_id} not exists.")

        user_groupId = user_res[5]

        specialityId = db.fetchone("SELECT parent_speciality FROM users_groups WHERE id = ?", (user_groupId,))[0]

        speciality = db.fetchone("SELECT speciality FROM specialities WHERE id = ?", (specialityId,))[0]

        user = User(sex=user_res[3],
                    course=user_res[4],
                    speciality=speciality,
                    group_id=user_groupId)
        return user

    @staticmethod
    def isMatch(priority, **kwargs: bool):
        priorities_table = _PRIORITIES[str(priority)]
        userData_table = kwargs

        priorities_keys = set(priorities_table.keys())
        userData_keys = set(userData_table.keys())
        if priorities_keys != userData_keys:
            raise KeyError("Current keys are not available.")

        shared_items = {k: priorities_table[k] for k in priorities_table if
                        k in userData_table and priorities_table[k] == userData_table[k]}

        if len(shared_items) != len(priorities_table):
            return False

        return True

    async def _get_partner(self, user_id1: int):
        user_sex1, user_course1, user_speciality1, user_group1 = self.get_userInfo(user_id1)

        queue_bytes = self.lrange("queue", 0, -1)

        queue_list_bytes = [x.decode("UTF-8") for x in queue_bytes]
        queue = [ast.literal_eval(x) for x in queue_list_bytes]

        x = 0
        priorities_number = len(_PRIORITIES)

        v_dumps = None
        while x != priorities_number:
            for i, v in enumerate(queue):
                user_id2, user2_QueueTime = v["user_id"], v["time_inQueue"]
                user_sex2, user_course2, user_speciality2, user_group2 = self.get_userInfo(user_id2)

                current_unixStamp = int(time.time())

                if user_sex1 != user_sex2 and current_unixStamp - user2_QueueTime >= MAX_IN_QUEUE_TIME:
                    v_dumps = json.dumps(v)
                    self.__red.lrem("queue", 0, v_dumps)
                    return user_id2

                if self.isMatch(x, sex=user_sex1 == user_sex2,
                                speciality=user_speciality1 == user_speciality2,
                                course=user_course1 == user_course2,
                                user_group=user_group1 == user_group2):
                    v_dumps = json.dumps(v)
                    self.__red.lrem("queue", 0, v_dumps)
                    return user_id2

            x += 1

        if queue: # if nobody is found by priorities - match without them
            return queue[0]["user_id"]

    async def _get_meetingTime(self):
        """
        Returns meeting time and time when to send links on conference
        _get_meetingTime() -> (meeting_datetime, meeting_timeUnix, send_link_now=True)
        """
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")

        meetings_times = db.fetchall("SELECT time FROM meetings")
        if len(meetings_times) < JITSI_MAX_ROOMS:
            return current_time + timedelta(minutes=1), int(time.mktime(current_time.timetuple())), True

        meetings_dateTimes_list = [datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S") for t in meetings_times]

        min_time = min(meetings_dateTimes_list)
        if min_time < current_time:
            raise GetTimeError(f"Old conference record with 'time' = {min_time} is found in database. Unable to get time")

        return min_time + timedelta(minutes=15), int(time.mktime(min_time.timetuple())), False

    async def create_meeting(self, user_id: int) -> Meeting:
        candidate_id = await self._get_partner(user_id)
        if not candidate_id:
            current_unixStamp = int(time.time())

            queue_user = QueueUser(user_id=user_id, inQueue_since=current_unixStamp)
            self.list_append("queue", queue_user)
            raise ExistenceError(f"No candidate now for {user_id}. Added to queue")

        meeting_datetime, meeting_time_unix, send_link_now = await self._get_meetingTime()

        room_name = self._get_room_name()

        first_link = await self._generate_link(user_id, meeting_time_unix, room_name)
        second_link = await self._generate_link(candidate_id, meeting_time_unix, room_name)

        user1_pk = db.fetchone("SELECT id FROM users WHERE telegram_id = ?", (user_id,))[0]
        user2_pk = db.fetchone("SELECT id FROM users WHERE telegram_id = ?", (candidate_id,))[0]

        meeting = Meeting(user1_pk=user1_pk,
                          user2_pk=user2_pk,
                          link_1=first_link,
                          link_2=second_link,
                          meeting_time=(meeting_datetime, meeting_time_unix),
                          send_link_now=send_link_now
                          )

        return meeting

    def _get_room_name(self):
        return str(uuid.uuid4())

    async def _generate_link(self, user_id: int, meeting_time_unix: int, room_name: str):
        full_name = db.fetchone("SELECT full_name FROM users WHERE telegram_id = ?", (user_id,))[0]

        payload = {
            "context": {
                "user": {
                    "avatar": "https:/gravatar.com/avatar/abc123",
                    "name": full_name,
                    "email": "jdoe@example.com",
                    "id": "abcd:a1b2c3-d4e5f6-0abc1-23de-abcdef01fedcba",
                }
            },
            "aud": "jitsi",
            "iss": JITSI_APP_ID,
            "sub": JITSI_DOMAIN,
            "room": room_name,
            "exp": meeting_time_unix + JITSI_MEETING_TIME
        }
        encoded_jwt = jwt.encode(payload, JITSI_SECRET, algorithm="HS256")
        return JITSI_DOMAIN + '/' + room_name + f"?jwt={encoded_jwt}"
