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
    meeting_time_unix: Optional[int]

    user1_pk: int
    user2_pk: int

    link_1: str
    link_2: str


    def __iter__(self):
        if self.meeting_time_unix:
            return iter((self.meeting_time_datetime, self.meeting_time_unix,
                         self.user1_pk, self.user2_pk, self.link_1, self.link_2))

        return iter((self.meeting_time_datetime,
                     self.user1_pk, self.user2_pk,
                     self.link_1, self.link_2))


@dataclass
class User:
    sex: str
    course: int
    speciality: str
    group_id: int

    def __iter__(self):
        return iter((self.sex, self.course, self.speciality, self.group_id))
