from vk_teams_async_bot import State, StatesGroup


class WizardButtonStates(StatesGroup):
    choosing_size = State()
    choosing_crust = State()
    choosing_sauce = State()
    confirm = State()


class WizardTextStates(StatesGroup):
    entering_name = State()
    entering_email = State()
    entering_phone = State()
    confirm = State()


class WizardMixedStates(StatesGroup):
    choosing_event = State()
    entering_attendees = State()
    choosing_meal = State()
    entering_notes = State()
    confirm = State()


class ToggleStates(StatesGroup):
    settings = State()


class MultiSelectStates(StatesGroup):
    selecting = State()


class FileReceiveStates(StatesGroup):
    waiting_for_file = State()


class FilterDemoStates(StatesGroup):
    waiting_for_reply = State()
    waiting_for_forward = State()
    waiting_for_file = State()
    waiting_for_voice = State()
    waiting_for_mention = State()
