import random
import json
import ast
from dataclasses import dataclass
from db_instance import db
import datetime
import time
import uuid
from redis import Redis, StrictRedis
from cfg import *
import jwt
from utils.exceptions import *

PRIORITIES = {"0": {"sex": False, "course": True, "speciality": True, "user_group": False},
              "1": {"sex": False, "course": True, "speciality": False, "user_group": False},
              "2": {"sex": False, "course": True, "speciality": True, "user_group": True},
              "3": {"sex": False, "course": False, "speciality": True, "user_group": False},
              "4": {"sex": False, "course": False, "speciality": False, "user_group": False}}

AVAILABLE_TIMES = ["10:00:00", "10:20:00", "10:40:00",
                   "11:00:00", "11:20:00", "11:40:00",
                   "12:00:00", "12:20:00", "12:40:00",
                   "13:00:00", "13:20:00", "13:40:00",
                   "14:00:00", "14:20:00", "14:40:00",
                   "15:00:00", "15:20:00", "15:40:00",
                   "16:00:00", "16:20:00", "16:40:00",
                   "17:00:00", "17:20:00", "17:40:00",
                   "18:00:00", "18:20:00", "18:40:00",
                   "19:00:00", "19:20:00", "19:40:00",
                   "20:00:00", "20:20:00", "20:40:00"]


@dataclass
class QueueUser:
    user_id: int
    time_inQueue: int


class MeetingsManager:

    def __init__(self, red):
        if not any([isinstance(red, Redis), isinstance(red, StrictRedis)]):
            raise TypeError("Redis instance should be Redis or StrictRedis")
        self.red = red

    def _queueAppend(self, value: QueueUser):
        user_id, time_inQueue = value.user_id, value.time_inQueue
        dic = {"user_id": user_id, "time_inQueue": time_inQueue}
        dic_dumps = json.dumps(dic)
        self.red.rpush("queue", dic_dumps)

    def _queuePop(self):
        return self.red.lpop("queue")

    @staticmethod
    def get_userInfo(user_id: int):
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

        shared_items = {k: priorities_table[k] for k in priorities_table if
                        k in userData_table and priorities_table[k] == userData_table[k]}

        if len(shared_items) != len(priorities_table):
            return False

        return True

    async def _get_partner(self, user_id1: int):
        user_sex1, user_course1, user_speciality1, user_group1 = self.get_userInfo(user_id1)

        queue_bytes = self.red.lrange('queue', 0, -1)

        queue_list_bytes = [x.decode("UTF-8") for x in queue_bytes]
        queue = [ast.literal_eval(x) for x in queue_list_bytes]

        x = 0
        priorities_number = len(PRIORITIES)

        v_dumps = None
        while x != priorities_number:
            for i, v in enumerate(queue):
                user_id2, user2_QueueTime = v["user_id"], v["time_inQueue"]
                user_sex2, user_course2, user_speciality2, user_group2 = self.get_userInfo(user_id2)

                current_unixStamp = int(time.time())

                if user_sex1 != user_sex2 and current_unixStamp - user2_QueueTime >= MAX_IN_QUEUE_TIME:
                    v_dumps = json.dumps(v)
                    self.red.lrem("queue", 0, v_dumps)
                    return user_id2

                if self.isMatch(x, sex=user_sex1 == user_sex2,
                                speciality=user_speciality1 == user_speciality2,
                                course=user_course1 == user_course2,
                                user_group=user_group1 == user_group2):
                    v_dumps = json.dumps(v)
                    self.red.lrem("queue", 0, v_dumps)
                    return user_id2

            x += 1

    async def _get_meetingTime(self):
        for i, t in enumerate(AVAILABLE_TIMES):
            time_split = t.split(':')
            hour, minute, _ = time_split

            meetings_for_current_time = db.fetchall("SELECT * FROM meetings WHERE strftime('%H', time) = ? AND"
                                                    " strftime('%S', time) = ? ORDER BY time ASC", (hour, minute))
            today = datetime.date.today()

            current_time = time.strftime("%H:%M:%S")
            current_time = datetime.datetime.strptime(current_time, "%H:%M:%S")

            current_time = current_time.replace(year=today.year, month=today.month, day=today.day)

            t = datetime.datetime.strptime(t, "%H:%M:%S").replace(year=today.year, month=today.month, day=today.day)

            if current_time >= t:
                continue

            delta = (t - current_time).seconds

            if len(meetings_for_current_time) < JITSI_MAX_ROOMS:
                if delta < MIN_TIME_BEFORE_MEETING:
                    if i + 1 >= len(AVAILABLE_TIMES):  # If no time after --> break
                        break
                    next_available_time = datetime.datetime.strptime(AVAILABLE_TIMES[i + 1], "%H:%M:%S") \
                        .replace(year=today.year, month=today.month, day=today.day)

                    return next_available_time
                return t

    async def create_meeting(self, user_id: int):
        meeting_time = await self._get_meetingTime()
        if meeting_time is None:
            raise GetTimeError("Unable to get time now. For today meetings are over")

        candidate_id = await self._get_partner(user_id)
        if not candidate_id:
            current_unixStamp = int(time.time())

            queue_user = QueueUser(user_id=user_id, time_inQueue=current_unixStamp)
            self._queueAppend(queue_user)

            raise ExistenceError(f"No candidate now for {user_id}. Added to queue")

        meeting_time_unix = time.mktime(meeting_time.timetuple())

        first_link = await self._generate_link(user_id, meeting_time_unix)
        second_link = await self._generate_link(candidate_id, meeting_time_unix)


        # db.query("INSERT INTO meetings VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (None, user_id,
        #                                                                  candidate_id, first_link,
        #                                                                  second_link, meeting_time,
        #                                                                  "INACTIVE", "INACTIVE"))

        return meeting_time

    @staticmethod
    async def _generate_link(user_id, meeting_time_unix):
        full_name = db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))[2]

        uid = str(uuid.uuid4())
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
            "room": uid,
            "exp": meeting_time_unix + JITSI_MEETING_TIME
        }

        encoded_jwt = jwt.encode(payload, JITSI_SECRET, algorithm="HS256")
        return JITSI_DOMAIN + '/' + uid + f"?jwt={encoded_jwt}"
