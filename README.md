# Google Workspace Skill for Claude Code

Connect Gmail and Google Drive directly into [Claude Code](https://claude.ai/code) — read emails, search Drive, send messages, upload files, and more, all from a natural language chat.

Built by [TovTech](https://tovtech.org).

---

## What you can do

Once set up, just talk to Claude Code naturally:

| Request | What happens |
|---|---|
| "Show me my last 10 emails" | Lists recent inbox with subjects and senders |
| "Find Drive files about project X" | Full-text search across your Drive |
| "What files were created this week in this folder?" | Filters by creation date |
| "Send an email to X with subject Y" | Sends via Gmail |
| "Reply to this email thread" | Replies in the correct thread |
| "Upload this file to Drive" | Uploads a local file |
| "Share this file with user@example.com as editor" | Sets sharing permissions |
| "What changed recently in my Drive?" | Lists recently modified files |

---

## Files in this repo

| File | Purpose |
|---|---|
| `gdrive.py` | Python helper script — all Gmail + Drive operations |
| `google-workspace.md` | The Claude Code skill (place in `~/.claude/commands/`) |
| `setup-google-workspace.md` | Interactive setup wizard (place in `~/.claude/commands/`) |

---

## Quick setup

### 1. Download this repo

```bash
git clone https://github.com/TovTechOrg/google-workspace-skill
```

### 2. Place the setup skill in Claude Code

**Windows:**
```
copy setup-google-workspace.md %USERPROFILE%\.claude\commands\
```

**Mac/Linux:**
```bash
cp setup-google-workspace.md ~/.claude/commands/
```

### 3. Run the setup wizard

Open Claude Code and run:
```
/setup-google-workspace
```

The wizard will:
- Install required Python packages automatically
- Copy all files to the correct locations
- Guide you through creating Google Cloud credentials (one-time, ~10 min)
- Handle first-time authentication

That's it — no manual path editing required.

---

## Manual setup (advanced)

If you prefer to set up manually, see the full instructions inside [`google-workspace.md`](google-workspace.md).

### Requirements

- Python 3.9+
- A Google account
- Claude Code CLI

### Python dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Google Cloud credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Enable **Google Drive API** and **Gmail API**
4. Create **OAuth 2.0 credentials** (Desktop app type)
5. Add your email as a Test User under OAuth consent screen
6. Download the credentials JSON → save as `client secret.json`

### Place files

```
~/.claude/
├── gdrive.py
├── client secret.json
└── commands/
    ├── google-workspace.md
    └── setup-google-workspace.md
```

Update the two path constants at the top of `gdrive.py` to match your username.

### First authentication

```bash
py ~/.claude/gdrive.py emails
```

A browser window will open — approve the permissions once. A `drive_token.json` is saved and auto-refreshes from then on.

---

## Available operations

### Gmail

| CLI command | Function | Description |
|---|---|---|
| `emails [N]` | `list_emails(n)` | List recent emails |
| `emails_search "<query>"` | `search_emails(query)` | Search with Gmail syntax (`from:`, `is:unread`, `after:`) |
| `email <id>` | `get_email(id)` | Full email body |
| `thread <thread_id>` | `get_thread(id)` | Full thread conversation |
| `send <to> <subject> <body>` | `send_email(...)` | Send email |
| `reply <msg_id> <body>` | `reply_email(...)` | Reply in thread |
| `trash_email <id>` | `trash_email(id)` | Move to trash |
| `mark_read <id>` | `mark_read(id)` | Mark as read |
| `mark_unread <id>` | `mark_unread(id)` | Mark as unread |

### Drive

| CLI command | Function | Description |
|---|---|---|
| `list <folder_id>` | `list_folder(id)` | List files in folder |
| `list_date <folder_id> <YYYY-MM-DD>` | `list_folder_by_date(...)` | Files created after date |
| `recent [N]` | `recent_files(n)` | Recently modified files |
| `read <file_id>` | `read_doc(id)` | Read Doc/Sheet/Presentation |
| `search <query>` | `search_files(query)` | Full-text search |
| `info <file_id>` | `file_info(id)` | File metadata |
| `create_folder <name>` | `create_folder(name)` | Create folder |
| `create_doc <name>` | `create_doc(name)` | Create Google Doc |
| `upload <path>` | `upload_file(path)` | Upload local file |
| `download <id> <path>` | `download_file(...)` | Download to local |
| `move <id> <parent_id>` | `move_file(...)` | Move to folder |
| `rename <id> <name>` | `rename_file(...)` | Rename file |
| `trash_file <id>` | `trash_file(id)` | Move to trash |
| `share <id> <email> [role]` | `share_file(...)` | Share (reader/writer/commenter) |

---

## Re-authentication

If the token is ever revoked:

```bash
# Windows
del %USERPROFILE%\.claude\drive_token.json

# Mac/Linux
rm ~/.claude/drive_token.json
```

Then run any command — the browser will open once to re-authorize.

---

## License

MIT — free to use, modify, and share.
