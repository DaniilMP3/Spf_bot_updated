from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Union, Tuple


@dataclass
class QueueUser:
    user_id: int
    inQueue_since: int

    def __iter__(self):
        return iter((self.user_id, self.inQueue_since))


@dataclass
class Meeting:
    meeting_time: Union[Tuple[datetime, int]]
    send_link_now: bool

    user1_pk: int
    user2_pk: int

    link_1: str
    link_2: str

    def __iter__(self):

        return iter((self.user1_pk, self.user2_pk,
                     self.meeting_time, self.send_link_now,
                     self.link_1, self.link_2))


@dataclass
class User:
    sex: str
    course: int
    speciality: str
    group_id: int

    def __iter__(self):
        return iter((self.sex, self.course, self.speciality, self.group_id))
