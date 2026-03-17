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
    waiting_for_sticker = State()
    waiting_for_and = State()
    waiting_for_or = State()
    waiting_for_not = State()
    waiting_for_regexp_parts = State()
    waiting_for_nick_parts = State()
    waiting_for_email_regexp = State()
    waiting_for_tag = State()
    waiting_for_command = State()
    waiting_for_mention_user = State()
    waiting_for_text_filter = State()
    waiting_for_filetype = State()
    waiting_for_from_user = State()


class ChatAdminStates(StatesGroup):
    entering_title = State()
    entering_about = State()
    entering_rules = State()
    confirming_title = State()
    confirming_about = State()
    confirming_rules = State()
