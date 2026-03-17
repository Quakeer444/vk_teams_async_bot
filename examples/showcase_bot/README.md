# Showcase Bot

Comprehensive example demonstrating all features of `vk_teams_async_bot`.

## Setup

```bash
export BOT_TOKEN="your_bot_token_here"
export API_URL="https://api.internal.myteam.mail.ru"  # optional, this is the default
```

## Run

```bash
# From project root
python -m examples.showcase_bot.main
```

## Sections

| # | Section | Description |
|---|---------|-------------|
| 1 | Buttons | All 3 button styles, URL button, show_alert, url callback, keyboard composition (+) |
| 2 | Navigation | 4-level deep menu navigation with back buttons |
| 3 | Formatting | Format API, HTML mode, MarkdownV2 mode, ordered/unordered lists |
| 4 | Wizard (Buttons) | Multi-step pizza order wizard using buttons only |
| 5 | Wizard (Text) | Registration wizard with text input and validation |
| 6 | Wizard (Mixed) | Event registration combining buttons and text input |
| 7 | Toggle Settings | 5 boolean settings with ON/OFF visual toggle |
| 8 | Multi-Select | Language selector with visual selection and conditional "Next" |
| 9 | Files | Send/receive files, get_file_info, download, resend by file_id |
| 10 | Events | Handlers for edited/deleted/pinned/unpinned/members events |
| 11 | Message Ops | Reply, forward, edit, delete message operations |
| 12 | Filters | Part, text, composite (AND/OR/NOT), advanced (RegexpTextParts, NickFilter) |
| 13 | New Filters | ChatTypeFilter, ChatIdFilter, TextFilter, FileTypeFilter, FromUserFilter |
| 14 | Chat Ops | Chat info, typing/looking actions, pin/unpin |
| 15 | DI | Dependency injection: sync, async, generator, Annotated |
| 16 | Error Handling | APIError demo, error hierarchy, safe try/except patterns |
| 17 | Chat Admin | Read-only admin/members/blocked/pending, gated write (title/about/rules) |

## Architecture

- `main.py` -- bot setup, commands, middleware, lifecycle hooks
- `states.py` -- FSM state group definitions
- `keyboards.py` -- all keyboard builder functions
- `keyboards_extra.py` -- keyboards for new sections (new filters, errors, chat admin)
- `handlers/` -- one file per section, registered via `register_all_handlers()`

## Notes

- `MemoryStorage` is used for demo purposes only. In production, implement `BaseStorage` with a persistent backend (Redis, database, etc.).
- The bot uses `SessionTimeoutMiddleware` with a 10-minute timeout.
