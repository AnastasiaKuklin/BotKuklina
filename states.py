from aiogram.fsm.state import StatesGroup, State

class File(StatesGroup):
    sending_file = State()
    groupName = State()