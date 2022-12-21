from aiogram.dispatcher.filters.state import State, StatesGroup


class Register(StatesGroup):
    full_name = State()
    sex = State()
    speciality = State()
    course = State()
    group = State()
