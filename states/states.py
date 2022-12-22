from aiogram.dispatcher.filters.state import State, StatesGroup


class Register(StatesGroup):
    full_name = State()
    sex = State()
    course = State()
    speciality = State()
    group = State()


class EditHierarchy(StatesGroup):
    speciality = State()
    group = State()
