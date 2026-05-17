# /google-workspace

Access Gmail and Google Drive on behalf of the user. Replaces the broken `gmail-mcp` and `drive-mcp` MCP servers.

## Infrastructure

- **Helper script:** `~/.claude\gdrive.py`
- **Token file:** `~/.claude\drive_token.json` (auto-refreshes, no re-auth needed)
- **Client secret:** `~/.claude\client secret.json`
- **Scopes:** `drive` (full) + `gmail.modify` + `gmail.compose` + `gmail.readonly`

All operations run via:
```bash
py "~/.claude\gdrive.py" <cmd> [args]
```

Always add `2>&1` to commands.

---

## Gmail Operations

### List recent emails
```bash
py "~/.claude\gdrive.py" emails [N]
```
Returns: message ID, threadId, From, Subject, Date, snippet. Default N=5.

### Search emails (Gmail query syntax)
```bash
py "~/.claude\gdrive.py" emails_search "<query>" [N]
```
Gmail query examples: `from:someone@example.com`, `subject:invoice`, `after:2026/05/01`, `is:unread`, `has:attachment`

### Read full email
```bash
py "~/.claude\gdrive.py" email <message_id>
```

### Read full email thread
```bash
py "~/.claude\gdrive.py" thread <thread_id>
```
Returns all messages in the thread in order.

### Send email
```bash
py "~/.claude\gdrive.py" send "<to@email.com>" "<Subject>" "<body text>"
```
For multi-line body, use Python directly:
```bash
py -c "
import sys; sys.path.insert(0, ~/.claude')
import gdrive
gdrive.send_email('to@example.com', 'Subject', 'Body text here')
"
```

### Reply to an email
```bash
py "~/.claude\gdrive.py" reply <message_id> <body text>
```
Automatically uses the correct thread, subject (Re: ...), and recipient.

### Trash an email
```bash
py "~/.claude\gdrive.py" trash_email <message_id>
```

### Mark email read / unread
```bash
py "~/.claude\gdrive.py" mark_read <message_id>
py "~/.claude\gdrive.py" mark_unread <message_id>
```

---

## Drive Operations

### List files in a folder
```bash
py "~/.claude\gdrive.py" list <folder_id>
```
Folder ID is the last segment of the Drive URL:
`https://drive.google.com/drive/folders/FOLDER_ID_HERE`

### List files created after a date
```bash
py "~/.claude\gdrive.py" list_date <folder_id> <YYYY-MM-DD>
```
Returns files created on or after the given date with creation date and link.

### List recently modified files (all Drive)
```bash
py "~/.claude\gdrive.py" recent [N]
```
Default N=20. Returns files sorted by last modified time across all of Drive.

### Read a Google Doc / Sheet / Presentation
```bash
py "~/.claude\gdrive.py" read <file_id>
```
- Google Docs → plain text
- Sheets → CSV
- Presentations → plain text
- Other files → raw content

### Search Drive by text
```bash
py "~/.claude\gdrive.py" search "<query terms>"
```

### Get file metadata
```bash
py "~/.claude\gdrive.py" info <file_id>
```
Returns: id, name, mimeType, modifiedTime, createdTime, size, parents, webViewLink.

### Create a folder
```bash
py "~/.claude\gdrive.py" create_folder "<name>" [parent_folder_id]
```

### Create a new Google Doc
```bash
py "~/.claude\gdrive.py" create_doc "<name>" [parent_folder_id]
```

### Upload a local file
```bash
py "~/.claude\gdrive.py" upload "<local_path>" [parent_folder_id]
```
MIME type is auto-detected. Returns the new file's ID and link.

### Download a file
```bash
py "~/.claude\gdrive.py" download <file_id> "<local_path>"
```
Google Docs → .txt, Sheets → .csv, Presentations → .pdf, others → as-is.

### Move a file
```bash
py "~/.claude\gdrive.py" move <file_id> <new_parent_folder_id>
```

### Rename a file
```bash
py "~/.claude\gdrive.py" rename <file_id> "<new name>"
```

### Trash a Drive file
```bash
py "~/.claude\gdrive.py" trash_file <file_id>
```

### Share a file
```bash
py "~/.claude\gdrive.py" share <file_id> <email> [role]
```
Role options: `reader` (default), `writer`, `commenter`. Sends a notification email.

---

## Using as a Python module

For complex operations, import directly:
```python
import sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, ~/.claude')
import gdrive

# Gmail
emails = gdrive.list_emails(10, query='from:someone@example.com')
emails = gdrive.search_emails('is:unread after:2026/05/01', n=20)
body   = gdrive.get_email('MESSAGE_ID')['body']
thread = gdrive.get_thread('THREAD_ID')
gdrive.reply_email('MESSAGE_ID', 'Reply body here')
gdrive.trash_email('MESSAGE_ID')
gdrive.mark_read('MESSAGE_ID')

# Drive
files  = gdrive.list_folder('FOLDER_ID')
recent = gdrive.recent_files(n=10)
dated  = gdrive.list_folder_by_date('FOLDER_ID', '2026-05-12')
text   = gdrive.read_doc('FILE_ID')
hits   = gdrive.search_files('keyword')
info   = gdrive.file_info('FILE_ID')
folder = gdrive.create_folder('New Folder', parent_id='PARENT_ID')
doc    = gdrive.create_doc('New Doc', parent_id='PARENT_ID')
f      = gdrive.upload_file(r'C:\path\to\file.pdf', parent_id='PARENT_ID')
path   = gdrive.download_file('FILE_ID', r'C:\local\path\file')
gdrive.move_file('FILE_ID', 'NEW_PARENT_ID')
gdrive.rename_file('FILE_ID', 'New Name')
gdrive.trash_file('FILE_ID')
gdrive.share_file('FILE_ID', 'user@example.com', role='writer')
```

---

## Re-authentication (only if token is revoked)

```bash
rm "~/.claude/drive_token.json"
py "~/.claude\gdrive.py" emails
```

---

## Common patterns

### "Show me my last N emails"
```bash
py "~/.claude\gdrive.py" emails 10
```

### "Find unread emails from X"
```bash
py "~/.claude\gdrive.py" emails_search "from:x@example.com is:unread"
```

### "Show me the full conversation"
Get threadId from email, then:
```bash
py "~/.claude\gdrive.py" thread <threadId>
```

### "Files created this week in folder X"
```bash
py "~/.claude\gdrive.py" list_date <folder_id> 2026-05-12
```

### "What changed recently in my Drive?"
```bash
py "~/.claude\gdrive.py" recent 20
```

### "Upload this file and share with someone"
```bash
py "~/.claude\gdrive.py" upload "C:\path\to\file.pdf" <folder_id>
py "~/.claude\gdrive.py" share <new_file_id> user@example.com writer
```

---

## Error handling

| Error | Cause | Fix |
|-------|-------|-----|
| `insufficientPermissions 403` | Old token without new scopes | Delete token, re-auth |
| `File not found 404` | File ID wrong or no access | Verify URL / check sharing |
| `Token expired` | Should auto-refresh. If not: | Delete token, re-auth |
| `HttpError 400 export` | Binary file, can't export as text | Use `info` to check mimeType |
| `Invalid label` | Wrong label name in mark_read | Use `UNREAD` (uppercase) |
