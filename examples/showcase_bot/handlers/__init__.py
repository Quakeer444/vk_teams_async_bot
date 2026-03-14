from vk_teams_async_bot import Dispatcher
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from .buttons import register_buttons_handlers
from .chat_ops import register_chat_ops_handlers
from .di_demo import register_di_handlers
from .events import register_events_handlers
from .files import register_files_handlers
from .filters_demo import register_filters_handlers
from .formatting import register_formatting_handlers
from .messages import register_messages_handlers
from .multiselect import register_multiselect_handlers
from .navigation import register_navigation_handlers
from .toggles import register_toggle_handlers
from .wizard_buttons import register_wizard_buttons_handlers
from .wizard_mixed import register_wizard_mixed_handlers
from .wizard_text import register_wizard_text_handlers


def register_all_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    # 1. Button showcase
    register_buttons_handlers(dp)
    # 2. Navigation
    register_navigation_handlers(dp)
    # 3. Formatting
    register_formatting_handlers(dp)
    # 4. Wizard (buttons only)
    register_wizard_buttons_handlers(dp)
    # 5. Wizard (text input)
    register_wizard_text_handlers(dp, storage)
    # 6. Wizard (mixed)
    register_wizard_mixed_handlers(dp, storage)
    # 7. Toggle settings
    register_toggle_handlers(dp)
    # 8. Multi-select
    register_multiselect_handlers(dp)
    # 9. Files
    register_files_handlers(dp, storage)
    # 10. Messages
    register_messages_handlers(dp)
    # 11. Filters demo
    register_filters_handlers(dp, storage)
    # 12. Chat ops
    register_chat_ops_handlers(dp)
    # 13. DI
    register_di_handlers(dp)
    # 14. Events (register last -- catch-all event handlers)
    register_events_handlers(dp)
