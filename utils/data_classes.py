from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class QueueUser:
    user_id: int
    inQueue_since: int


@dataclass
class Meeting:
    meeting_time_datetime: datetime

    user_id1: int
    user_id2:  int

    link_1: str
    link_2: str

    meeting_time_unix: Optional[int]


@dataclass
class User:
    sex: str
    course: int
    speciality: str
    group_id: int

    def __iter__(self):
        return iter((self.sex, self.course, self.speciality, self.group_id))
