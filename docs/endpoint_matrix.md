# VK Teams Bot API — Endpoint Matrix

Generated from spec reconciliation (Phase 0).
Sources: `vkteams_botapi.json` (OpenAPI 3.0), `vk_teams_botapi_full.md` (Russian docs).

## Legend

| Marker | Meaning |
|--------|---------|
| cloud | Works in any environment |
| admin_required | Bot must be chat admin |
| onprem_only | On-premise builds only (requires `bot_api_private_methods` entry) |

## Global API Constraints

| Constraint | Value | Source |
|------------|-------|--------|
| Query string limit | 60 KB | `vk_teams_botapi_full.md` |
| Request body limit | 50 MB | `vk_teams_botapi_full.md` |
| Protocol | HTTPS | `vk_teams_botapi_full.md` |
| chatId format | Nickname or ID (since 29.01.2020) | `vk_teams_botapi_full.md` |
| Message deletion window | 48 hours | `vk_teams_botapi_full.md` |

## Input Validation Rules (Mutual Exclusions)

| Rule | Endpoints | Source |
|------|-----------|--------|
| `replyMsgId` XOR (`forwardChatId` + `forwardMsgId`) | sendText, sendFile, sendVoice | `vk_teams_botapi_full.md` |
| `forwardChatId` requires `forwardMsgId` (and vice versa) | sendText, sendFile, sendVoice | `vk_teams_botapi_full.md` |
| `parseMode` XOR `format` object | sendText, editText, sendFile, sendVoice | `vk_teams_botapi_full.md` |
| `userId` XOR `everyone` (exactly one required) | resolvePending | `vk_teams_botapi_full.md` |
| `url` XOR `callbackData` per button | inlineKeyboardMarkup buttons | `vkteams_botapi.json` |

## Endpoints (27 paths, 30 GET + 3 POST = 33 operations)

---

### 1. GET /self/get

Get bot info.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | format: `001.{digits}:{digits}` | `vkteams_botapi.json` |

**Response:** `{ userId, nick, firstName?, about?, photo? [{url}] }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/self/get`

---

### 2. GET /messages/sendText

Send text message.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | nickname or ID | `vkteams_botapi.json` |
| text | string | yes | supports `@[userId]` mentions | `vkteams_botapi.json` |
| replyMsgId | array[integer] | no | XOR forwardChatId+forwardMsgId | `vk_teams_botapi_full.md` |
| forwardChatId | string | no | requires forwardMsgId | `vk_teams_botapi_full.md` |
| forwardMsgId | array[integer] | no | requires forwardChatId | `vk_teams_botapi_full.md` |
| inlineKeyboardMarkup | array[array] | no | 2D button array | `vkteams_botapi.json` |
| format | object | no | XOR parseMode | `vkteams_botapi.json` |
| parseMode | string | no | enum: MarkdownV2, HTML; XOR format | `vkteams_botapi.json` |

**Response:** `{ ok: bool, msgId: string }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/messages/sendText`

---

### 3. GET /messages/sendFile

Send file by previously uploaded fileId.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| fileId | string | yes | | `vkteams_botapi.json` |
| caption | string | no | supports formatting | `vkteams_botapi.json` |
| replyMsgId | array[integer] | no | XOR forwardChatId+forwardMsgId | `vk_teams_botapi_full.md` |
| forwardChatId | string | no | requires forwardMsgId | `vk_teams_botapi_full.md` |
| forwardMsgId | array[integer] | no | requires forwardChatId | `vk_teams_botapi_full.md` |
| inlineKeyboardMarkup | array[array] | no | | `vkteams_botapi.json` |
| format | object | no | XOR parseMode | `vkteams_botapi.json` |
| parseMode | string | no | enum: MarkdownV2, HTML | `vkteams_botapi.json` |

**Response:** `{ ok: bool, msgId: string }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/messages/sendFile` (GET)

---

### 4. POST /messages/sendFile

Upload and send file.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | query param | `vkteams_botapi.json` |
| chatId | string | yes | query param | `vkteams_botapi.json` |
| file | binary | yes | multipart/form-data, field name "file" | `vkteams_botapi.json` |
| caption | string | no | query param | `vkteams_botapi.json` |
| replyMsgId | array[integer] | no | XOR forwardChatId+forwardMsgId | `vk_teams_botapi_full.md` |
| forwardChatId | string | no | requires forwardMsgId | `vk_teams_botapi_full.md` |
| forwardMsgId | array[integer] | no | requires forwardChatId | `vk_teams_botapi_full.md` |
| inlineKeyboardMarkup | array[array] | no | | `vkteams_botapi.json` |
| format | object | no | XOR parseMode | `vkteams_botapi.json` |
| parseMode | string | no | enum: MarkdownV2, HTML | `vkteams_botapi.json` |

**Response:** `{ ok: bool, fileId: string, msgId: string }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/messages/sendFile` (POST)

---

### 5. GET /messages/sendVoice

Send voice message by fileId.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| fileId | string | yes | | `vkteams_botapi.json` |
| replyMsgId | array[integer] | no | XOR forwardChatId+forwardMsgId | `vk_teams_botapi_full.md` |
| forwardChatId | string | no | requires forwardMsgId | `vk_teams_botapi_full.md` |
| forwardMsgId | array[integer] | no | requires forwardChatId | `vk_teams_botapi_full.md` |
| inlineKeyboardMarkup | array[array] | no | | `vkteams_botapi.json` |

**Response:** `{ ok: bool, msgId: string }`
**Environment:** cloud
**Note:** Client expects aac, ogg, or m4a format
**Source:** `vkteams_botapi.json` path `/messages/sendVoice` (GET)

---

### 6. POST /messages/sendVoice

Upload and send voice message.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | query param | `vkteams_botapi.json` |
| chatId | string | yes | query param | `vkteams_botapi.json` |
| file | binary | yes | multipart/form-data, field name "file" | `vkteams_botapi.json` |
| replyMsgId | array[integer] | no | XOR forwardChatId+forwardMsgId | `vk_teams_botapi_full.md` |
| forwardChatId | string | no | requires forwardMsgId | `vk_teams_botapi_full.md` |
| forwardMsgId | array[integer] | no | requires forwardChatId | `vk_teams_botapi_full.md` |
| inlineKeyboardMarkup | array[array] | no | | `vkteams_botapi.json` |

**Response:** `{ ok: bool, fileId: string, msgId: string }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/messages/sendVoice` (POST)

---

### 7. GET /messages/editText

Edit text message.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| msgId | integer | yes | | `vkteams_botapi.json` |
| text | string | yes | | `vkteams_botapi.json` |
| inlineKeyboardMarkup | array[array] | no | | `vkteams_botapi.json` |
| format | object | no | XOR parseMode | `vkteams_botapi.json` |
| parseMode | string | no | enum: MarkdownV2, HTML | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/messages/editText`

---

### 8. GET /messages/deleteMessages

Delete messages.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| msgId | array[integer] | yes | messages must be < 48h old | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** cloud
**Note:** Bot can delete own messages in private/group; any message in group if admin
**Source:** `vkteams_botapi.json` path `/messages/deleteMessages`

---

### 9. GET /messages/answerCallbackQuery

Answer callback query from inline keyboard button press.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| queryId | string | yes | from callbackQuery event | `vkteams_botapi.json` |
| text | string | no | | `vkteams_botapi.json` |
| showAlert | boolean | no | default false | `vkteams_botapi.json` |
| url | string | no | | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** cloud
**Note:** Does NOT require token. Bot MUST respond to every callbackQuery.
**Source:** `vkteams_botapi.json` path `/messages/answerCallbackQuery`

---

### 10. GET /chats/createChat

Create new chat.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| name | string | yes | | `vkteams_botapi.json` |
| about | string | no | | `vkteams_botapi.json` |
| rules | string | no | | `vkteams_botapi.json` |
| members | array | no | format: `[{"sn":"userId"}]` | `vkteams_botapi.json` |
| public | string | no | "true"/"false" (NOT boolean) | `vkteams_botapi.json` |
| defaultRole | string | no | "member" for groups, "readonly" for channels | `vk_teams_botapi_full.md` |
| joinModeration | string | no | "true"/"false" (NOT boolean) | `vkteams_botapi.json` |

**Response:** `{ sn: string }` (chat ID)
**Environment:** onprem_only (requires `bot_api_private_methods` entry)
**Source:** `vkteams_botapi.json` path `/chats/createChat`

---

### 11. POST /chats/avatar/set

Set chat avatar.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | query param | `vkteams_botapi.json` |
| chatId | string | yes | query param | `vkteams_botapi.json` |
| image | binary | yes | multipart/form-data, field name "image" | `vkteams_botapi.json` |

**Response:** `{ ok: bool, description?: string }` (ok=false possible with description e.g. "Image is porn")
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/avatar/set`

---

### 12. GET /chats/members/add

Add members to chat.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| members | array | yes | format: `[{"sn":"userId"}]` | `vkteams_botapi.json` |

**Response:** `{ ok: bool, failures?: [{ id: string, error: string }] }` (partial success possible)
**Environment:** onprem_only (requires `bot_api_private_methods` entry)
**Source:** `vkteams_botapi.json` path `/chats/members/add`

---

### 13. GET /chats/members/delete

Delete members from chat.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| members | array | yes | format: `[{"sn":"userId"}]` | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/members/delete`

---

### 14. GET /chats/sendActions

Send chat actions (typing indicator).

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| actions | array[string] | yes | enum: "typing", "looking"; empty = stop | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** cloud
**Note:** Must re-send every 10 seconds while action continues; send empty to stop
**Source:** `vkteams_botapi.json` path `/chats/sendActions`

---

### 15. GET /chats/getInfo

Get chat info.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |

**Response:** Discriminated by `type` field:
- **private:** `{ type, firstName, lastName?, nick?, about?, isBot?, language?, photo? }`
- **group:** `{ type, title, about?, rules?, inviteLink?, public?, joinModeration? }`
- **channel:** `{ type, title, about?, rules?, inviteLink?, public?, joinModeration? }`

**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/chats/getInfo`

---

### 16. GET /chats/getAdmins

Get chat admins list.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |

**Response:** `{ admins: [ { userId, creator?: bool } | { userId } ] }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/chats/getAdmins`

---

### 17. GET /chats/getMembers

Get chat members list with cursor pagination.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| cursor | string | no | from previous getMembers response | `vkteams_botapi.json` |

**Response:** `{ members: [ { userId, creator?: bool } | { userId, admin?: bool } | { userId } ], cursor?: string }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/chats/getMembers`

---

### 18. GET /chats/getBlockedUsers

Get blocked users list.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |

**Response:** `{ users: [{ userId }] }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/getBlockedUsers`

---

### 19. GET /chats/getPendingUsers

Get pending users list.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |

**Response:** `{ users: [{ userId }] }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/getPendingUsers`

---

### 20. GET /chats/blockUser

Block user in chat.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| userId | string | yes | | `vkteams_botapi.json` |
| delLastMessages | boolean | no | delete user's recent messages | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/blockUser`

---

### 21. GET /chats/unblockUser

Unblock user in chat.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| userId | string | yes | | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/unblockUser`

---

### 22. GET /chats/resolvePending

Resolve pending users (approve/reject).

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| approve | boolean | yes | | `vkteams_botapi.json` |
| userId | string | conditional | XOR everyone; exactly one required | `vk_teams_botapi_full.md` |
| everyone | boolean | conditional | XOR userId; exactly one required | `vk_teams_botapi_full.md` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/resolvePending`

---

### 23. GET /chats/setTitle

Set chat title.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| title | string | yes | | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/setTitle`

---

### 24. GET /chats/setAbout

Set chat description.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| about | string | yes | | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/setAbout`

---

### 25. GET /chats/setRules

Set chat rules.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| rules | string | yes | | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/setRules`

---

### 26. GET /chats/pinMessage

Pin message in chat.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| msgId | integer | yes | | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/pinMessage`

---

### 27. GET /chats/unpinMessage

Unpin message in chat.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| chatId | string | yes | | `vkteams_botapi.json` |
| msgId | integer | yes | | `vkteams_botapi.json` |

**Response:** `{ ok: bool }`
**Environment:** admin_required
**Source:** `vkteams_botapi.json` path `/chats/unpinMessage`

---

### 28. GET /files/getInfo

Get file info.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| fileId | string | yes | | `vkteams_botapi.json` |

**Response:** `{ type: string, size: integer, filename: string, url: string }`
**Environment:** cloud
**Source:** `vkteams_botapi.json` path `/files/getInfo`

---

### 29. GET /events/get

Long-poll for events.

| Parameter | Type | Required | Constraints | Source |
|-----------|------|----------|-------------|--------|
| token | string | yes | | `vkteams_botapi.json` |
| lastEventId | integer | yes | 0 for first call, then max known eventId | `vkteams_botapi.json` |
| pollTime | integer | yes | seconds to hold connection open | `vkteams_botapi.json` |

**Response:** `{ events: [ { eventId, type, payload } ] }`

Event types (8 documented):
1. `newMessage` — msgId, chat, from, timestamp, text?, format?, parts?
2. `editedMessage` — msgId, chat, from, timestamp, editedTimestamp, text?, format?
3. `deletedMessage` — msgId, chat, timestamp
4. `pinnedMessage` — msgId, chat, from, text?, format?, timestamp
5. `unpinnedMessage` — msgId, chat, timestamp
6. `newChatMembers` — chat, newMembers[], addedBy
7. `leftChatMembers` — chat, leftMembers[], removedBy
8. `callbackQuery` — queryId, chat, from, message, callbackData

**Environment:** cloud
**Note:** Connection held open until event or pollTime; first call uses lastEventId=0
**Source:** `vkteams_botapi.json` path `/events/get`

---

## Discrepancy Resolution

| Issue | Resolution | Rationale |
|-------|-----------|-----------|
| `docs/README.md` references `API_REFERENCE.md` | Does not exist; redirect to this matrix | File never created |
| `docs/README.md` lists `sendTextWithDeeplink` | Unconfirmed, out of v1.0.0 scope | Not in OpenAPI spec |
| `docs/README.md` lists 3 thread endpoints | Unconfirmed, out of v1.0.0 scope | Not in OpenAPI spec |
| `chats/avatar/set` not in existing code | Confirmed in OpenAPI, must implement | Present in `vkteams_botapi.json` |
| `changedChatInfo` event type in code | Undocumented: no schema in OpenAPI | Route to `RawUnknownEvent` in v1.0.0 |
| `answerCallbackQuery` missing token | Confirmed: endpoint does NOT require token | OpenAPI spec omits token param |

## Unconfirmed Endpoints (excluded from v1.0.0)

| Endpoint | Source | Status |
|----------|--------|--------|
| `/messages/sendTextWithDeeplink` | `docs/README.md` only | Not in OpenAPI; excluded |
| `/threads/add` | `docs/README.md` only | Not in OpenAPI; excluded |
| `/threads/subscribers/get` | `docs/README.md` only | Not in OpenAPI; excluded |
| `/threads/autosubscribe` | `docs/README.md` only | Not in OpenAPI; excluded |
