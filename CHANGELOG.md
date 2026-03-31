# Changelog

## 1.1.0 (2026-03-31)

### New Features

- `StatesGroupFilter` for matching any state within an FSM states group
- `StateFilter` extended: wildcard (`"*"`) and `None` matching (match "no state")
- Comprehensive DEBUG logging across all key modules (bot, dispatcher, handlers, middleware, FSM, client, methods)

### Bug Fixes

- Redis FSM: use `WATCH/MULTI` for race-safe `update_data` (fixes race condition on concurrent updates)
- `PinnedMessageEvent`: add missing `format_` field
- Export previously undocumented types from `__init__.py`
- `close()` now properly stops polling + adds timeout to post-cancel gather
- Remove unreachable return after `sys.exit` in signal handling

### Security

- Sanitize tokens in tracebacks (not just logs)
- Support multiple tokens in sanitizing log filter
- Cover bot logger with sanitizing filter
- Pin GitHub Actions by SHA (supply chain protection)

### Documentation

- Expand README: full API reference, event models, scheduled notifications, rate limiting, table of contents
- Document `StatesGroupFilter` and `StateFilter` modes (wildcard/None)

### Tests

- E2E test suite: dispatcher + real Bot API (FSM, middleware, pipeline)
- Live tests: field validation and error cases (chats, files, messages)
- Unit tests: FSM dispatch integration, edge cases (drain_tasks, polling loop, context manager, close)
- Refactor: extract shared event builders to `tests/helpers.py`

### Chore

- Pre-commit hooks: black, isort
- `.coveragerc` for coverage configuration
- `CODEOWNERS` for automatic review assignment
- `context7.json` for library ownership verification

## 1.0.0 (2026-03-21)

This is a major release with a full rewrite of the library architecture. See [MIGRATION.md](MIGRATION.md) for upgrade instructions.

### Breaking Changes

- **Package structure**: flat modules replaced with nested packages (`types/`, `methods/`, `handlers/`, `filters/`, `fsm/`, `middleware/`, `client/`)
- **Event model**: `Event` (dict wrapper) replaced with typed Pydantic models (`NewMessageEvent`, `EditedMessageEvent`, `CallbackQueryEvent`, etc.)
- **Bot methods**: all methods now return Pydantic models instead of raw dicts
- **Bot lifecycle**: `Bot` is now a context manager; `start_polling()` requires a `Dispatcher` argument
- **Handler classes**: `BotButtonCommandHandler` renamed to `CallbackQueryHandler`
- **Filter system**: filters use typed model attributes (`event.chat.chat_id`) instead of raw dict access (`event.data["chat"]["chatId"]`)
- **FSM**: `DictUserState` replaced by `MemoryStorage` + `FSMContext`; storage key changed from `user_id` to `(chat_id, user_id)`
- **Middleware**: `Middleware` base class replaced by `BaseMiddleware` with `__call__(handler, event, data)` protocol
- **Session timeout**: moved from built-in behavior to optional `SessionTimeoutMiddleware`
- **Imports**: all public API available from top-level `vk_teams_async_bot` package

### New Features

- Full VK Teams Bot API coverage: 27 endpoints implemented (was 9)
- Typed event models for all 8 documented event types with Pydantic v2
- Forward-compatible event parsing: unknown event types routed to `RawUnknownEvent` instead of raising
- Decorator shortcuts for handler registration: `@dp.message()`, `@dp.callback_query()`, etc.
- Filter composition with `&`, `|`, `~` operators
- `FSMContext` with `(chat_id, user_id)` scoping -- same user can have different states in different chats
- Exponential backoff retry with jitter (`RetryPolicy`)
- Structured error hierarchy: `VKTeamsError` -> `APIError`, `ServerError`, `NetworkError`, `TimeoutError`
- HTTP 200 + `ok=false` responses properly detected and raised as `APIError`
- Partial success handling for `members/add` endpoint (`PartialSuccessResponse`)
- Client-side input validation (mutual exclusion rules for reply/forward, parseMode/format, etc.)
- `on_startup` / `on_shutdown` lifecycle hooks on `Bot`
- Graceful shutdown with SIGINT/SIGTERM handling
- CI workflows for lint, type-check, and tests

### New API Methods

- `create_chat` (on-prem only)
- `set_chat_avatar`
- `add_chat_members` (on-prem only)
- `delete_chat_members`
- `send_chat_actions`
- `get_chat_info`
- `get_chat_admins`
- `get_chat_members`
- `get_blocked_users`
- `get_pending_users`
- `block_user`
- `unblock_user`
- `resolve_pending`
- `set_chat_title`
- `set_chat_about`
- `set_chat_rules`
- `pin_message`
- `unpin_message`
- `get_file_info`

### Bug Fixes

- `LeftChatMembersEvent` now preserves the `removedBy` field (was dropped)
- `StateFilter` uses correct `(chat_id, user_id)` key instead of broken dict path
- `sendVoice` GET/POST mapping corrected

### Removed

- `timer.py` debug utility
- `local_.config` dependency in examples (replaced with `os.environ`)
- Old flat module files (`client_session.py`, `constants.py`, `events.py`, `filter.py`, `handler.py`, `helpers.py`, `middleware.py`, `state.py`)
