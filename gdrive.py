"""
Google Workspace helper (Gmail + Drive).
Replaces broken gmail-mcp / drive-mcp.
Token saved at: ~/.claude/drive_token.json
Re-auth only needed if token is revoked.

CLI usage:
  py gdrive.py emails [N]                        -- list N recent emails (default 5)
  py gdrive.py emails_search <query> [N]         -- search emails (Gmail query syntax)
  py gdrive.py email <id>                        -- full body of one email
  py gdrive.py thread <thread_id>                -- full email thread
  py gdrive.py send <to> <subject> <body>        -- send email
  py gdrive.py reply <message_id> <body>         -- reply to an email thread
  py gdrive.py trash_email <message_id>          -- move email to trash
  py gdrive.py mark_read <message_id>            -- mark email as read
  py gdrive.py mark_unread <message_id>          -- mark email as unread
  py gdrive.py list <folder_id>                  -- list files in Drive folder
  py gdrive.py list_date <folder_id> <YYYY-MM-DD> -- list files created after date
  py gdrive.py recent [N]                        -- list N most recently modified files
  py gdrive.py read <file_id>                    -- read Google Doc as plain text
  py gdrive.py search <query>                    -- search Drive by text
  py gdrive.py info <file_id>                    -- metadata of a file
  py gdrive.py create_folder <name> [parent_id] -- create a new Drive folder
  py gdrive.py create_doc <name> [parent_id]    -- create a new empty Google Doc
  py gdrive.py upload <local_path> [parent_id]  -- upload a local file to Drive
  py gdrive.py download <file_id> <local_path>  -- download a Drive file locally
  py gdrive.py move <file_id> <new_parent_id>   -- move file to a different folder
  py gdrive.py rename <file_id> <new_name>      -- rename a file
  py gdrive.py trash_file <file_id>             -- move Drive file to trash
  py gdrive.py share <file_id> <email> [role]   -- share file (role: reader/writer/commenter)
"""
import sys, os, base64, json, mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

_CLAUDE_DIR   = os.path.join(os.path.expanduser('~'), '.claude')
CLIENT_SECRET = os.path.join(_CLAUDE_DIR, 'client secret.json')
TOKEN_FILE    = os.path.join(_CLAUDE_DIR, 'drive_token.json')
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
]

def _creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return creds

def gmail():  return build('gmail', 'v1', credentials=_creds())
def drive():  return build('drive', 'v3', credentials=_creds())

# ── Gmail ──────────────────────────────────────────────

def list_emails(n=5, query=''):
    svc = gmail()
    params = dict(userId='me', maxResults=int(n))
    if query:
        params['q'] = query
    msgs = svc.users().messages().list(**params).execute().get('messages', [])
    results = []
    for m in msgs:
        msg = svc.users().messages().get(
            userId='me', id=m['id'], format='metadata',
            metadataHeaders=['Subject', 'From', 'To', 'Date']
        ).execute()
        h = {x['name']: x['value'] for x in msg['payload']['headers']}
        h['id'] = m['id']
        h['threadId'] = msg.get('threadId', '')
        h['snippet'] = msg.get('snippet', '')
        results.append(h)
    return results

def search_emails(query, n=10):
    """Search emails using Gmail query syntax (from:, subject:, after:, etc.)"""
    return list_emails(n=n, query=query)

def get_email(msg_id):
    svc = gmail()
    msg = svc.users().messages().get(userId='me', id=msg_id, format='full').execute()
    h = {x['name']: x['value'] for x in msg['payload']['headers']}

    def extract_body(payload):
        if payload.get('body', {}).get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        for part in payload.get('parts', []):
            if part['mimeType'] in ('text/plain', 'text/html'):
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            result = extract_body(part)
            if result:
                return result
        return ''

    return {**h, 'id': msg_id, 'threadId': msg.get('threadId', ''), 'body': extract_body(msg['payload'])}

def get_thread(thread_id):
    """Get all messages in an email thread."""
    svc = gmail()
    thread = svc.users().threads().get(userId='me', id=thread_id, format='full').execute()
    results = []
    for msg in thread.get('messages', []):
        h = {x['name']: x['value'] for x in msg['payload']['headers']}
        def extract_body(payload):
            if payload.get('body', {}).get('data'):
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
            for part in payload.get('parts', []):
                if part['mimeType'] in ('text/plain', 'text/html'):
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                result = extract_body(part)
                if result:
                    return result
            return ''
        results.append({**h, 'id': msg['id'], 'body': extract_body(msg['payload'])})
    return results

def send_email(to, subject, body, html=False):
    mime = MIMEText(body, 'html' if html else 'plain', 'utf-8')
    mime['to'] = to
    mime['subject'] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    gmail().users().messages().send(userId='me', body={'raw': raw}).execute()
    return f"Sent to {to}"

def reply_email(message_id, body, html=False):
    """Reply to an email thread."""
    svc = gmail()
    orig = svc.users().messages().get(userId='me', id=message_id, format='metadata',
                                       metadataHeaders=['Subject', 'From', 'To', 'Message-ID']).execute()
    headers = {x['name']: x['value'] for x in orig['payload']['headers']}
    thread_id = orig.get('threadId', '')

    reply_to = headers.get('From', '')
    subject = headers.get('Subject', '')
    if not subject.lower().startswith('re:'):
        subject = 'Re: ' + subject

    mime = MIMEText(body, 'html' if html else 'plain', 'utf-8')
    mime['to'] = reply_to
    mime['subject'] = subject
    if headers.get('Message-ID'):
        mime['In-Reply-To'] = headers['Message-ID']
        mime['References'] = headers['Message-ID']

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    svc.users().messages().send(userId='me', body={'raw': raw, 'threadId': thread_id}).execute()
    return f"Replied to {reply_to}"

def trash_email(message_id):
    """Move an email to trash."""
    gmail().users().messages().trash(userId='me', id=message_id).execute()
    return f"Moved {message_id} to trash"

def mark_read(message_id):
    """Mark email as read."""
    gmail().users().messages().modify(
        userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}
    ).execute()
    return f"Marked {message_id} as read"

def mark_unread(message_id):
    """Mark email as unread."""
    gmail().users().messages().modify(
        userId='me', id=message_id, body={'addLabelIds': ['UNREAD']}
    ).execute()
    return f"Marked {message_id} as unread"

# ── Drive ──────────────────────────────────────────────

def list_folder(folder_id, limit=50):
    res = drive().files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id,name,mimeType,modifiedTime,createdTime,size)",
        orderBy="modifiedTime desc",
        pageSize=int(limit)
    ).execute()
    return res.get('files', [])

def list_folder_by_date(folder_id, after_date, limit=50):
    """List files in a folder created after a given date (YYYY-MM-DD)."""
    res = drive().files().list(
        q=f"'{folder_id}' in parents and createdTime >= '{after_date}T00:00:00' and trashed=false",
        fields="files(id,name,mimeType,createdTime,modifiedTime,webViewLink)",
        orderBy="createdTime desc",
        pageSize=int(limit)
    ).execute()
    return res.get('files', [])

def recent_files(n=20):
    """List the N most recently modified files across all of Drive."""
    res = drive().files().list(
        q="trashed=false",
        fields="files(id,name,mimeType,modifiedTime,webViewLink)",
        orderBy="modifiedTime desc",
        pageSize=int(n)
    ).execute()
    return res.get('files', [])

def read_doc(file_id):
    svc = drive()
    meta = svc.files().get(fileId=file_id, fields='mimeType,name').execute()
    mime = meta['mimeType']
    if 'google-apps.document' in mime:
        return svc.files().export(fileId=file_id, mimeType='text/plain').execute().decode('utf-8')
    elif 'google-apps.spreadsheet' in mime:
        return svc.files().export(fileId=file_id, mimeType='text/csv').execute().decode('utf-8')
    elif 'google-apps.presentation' in mime:
        return svc.files().export(fileId=file_id, mimeType='text/plain').execute().decode('utf-8')
    else:
        content = svc.files().get_media(fileId=file_id).execute()
        return content.decode('utf-8', errors='replace') if isinstance(content, bytes) else str(content)

def search_files(query, limit=20):
    res = drive().files().list(
        q=f"fullText contains '{query}' and trashed=false",
        fields="files(id,name,mimeType,modifiedTime,webViewLink)",
        orderBy="modifiedTime desc",
        pageSize=int(limit)
    ).execute()
    return res.get('files', [])

def file_info(file_id):
    return drive().files().get(
        fileId=file_id,
        fields='id,name,mimeType,modifiedTime,createdTime,size,parents,webViewLink'
    ).execute()

def create_folder(name, parent_id=None):
    """Create a new folder in Drive."""
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        meta['parents'] = [parent_id]
    f = drive().files().create(body=meta, fields='id,name,webViewLink').execute()
    return f

def create_doc(name, parent_id=None):
    """Create a new empty Google Doc."""
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.document'}
    if parent_id:
        meta['parents'] = [parent_id]
    f = drive().files().create(body=meta, fields='id,name,webViewLink').execute()
    return f

def upload_file(local_path, parent_id=None):
    """Upload a local file to Drive."""
    name = os.path.basename(local_path)
    mime_type, _ = mimetypes.guess_type(local_path)
    mime_type = mime_type or 'application/octet-stream'
    meta = {'name': name}
    if parent_id:
        meta['parents'] = [parent_id]
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    f = drive().files().create(body=meta, media_body=media, fields='id,name,webViewLink').execute()
    return f

def download_file(file_id, local_path):
    """Download a Drive file to a local path."""
    svc = drive()
    meta = svc.files().get(fileId=file_id, fields='mimeType,name').execute()
    mime = meta['mimeType']

    if 'google-apps' in mime:
        export_map = {
            'application/vnd.google-apps.document': ('text/plain', '.txt'),
            'application/vnd.google-apps.spreadsheet': ('text/csv', '.csv'),
            'application/vnd.google-apps.presentation': ('application/pdf', '.pdf'),
        }
        export_mime, ext = export_map.get(mime, ('application/pdf', '.pdf'))
        if not local_path.endswith(ext):
            local_path += ext
        content = svc.files().export(fileId=file_id, mimeType=export_mime).execute()
        with open(local_path, 'wb') as f:
            f.write(content)
    else:
        request = svc.files().get_media(fileId=file_id)
        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
    return local_path

def move_file(file_id, new_parent_id):
    """Move a file to a different folder."""
    svc = drive()
    f = svc.files().get(fileId=file_id, fields='parents').execute()
    old_parents = ','.join(f.get('parents', []))
    updated = svc.files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=old_parents,
        fields='id,name,parents'
    ).execute()
    return updated

def rename_file(file_id, new_name):
    """Rename a file in Drive."""
    f = drive().files().update(fileId=file_id, body={'name': new_name}, fields='id,name').execute()
    return f

def trash_file(file_id):
    """Move a Drive file to trash."""
    drive().files().trash(fileId=file_id).execute()
    return f"File {file_id} moved to trash"

def share_file(file_id, email, role='reader'):
    """Share a file with someone. Role: reader, writer, commenter."""
    perm = drive().permissions().create(
        fileId=file_id,
        body={'type': 'user', 'role': role, 'emailAddress': email},
        sendNotificationEmail=True,
        fields='id'
    ).execute()
    return f"Shared with {email} as {role} (permission id: {perm['id']})"

# ── CLI ────────────────────────────────────────────────

if __name__ == '__main__':
    import warnings; warnings.filterwarnings('ignore')
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'

    if cmd == 'emails':
        n = sys.argv[2] if len(sys.argv) > 2 else 5
        for e in list_emails(n):
            print(f"[{e['id']}]  {e.get('Date','')[:20]}")
            print(f"  From: {e.get('From','')}")
            print(f"  Subj: {e.get('Subject','')}")
            print(f"  {e.get('snippet','')[:100]}")
            print()

    elif cmd == 'emails_search' and len(sys.argv) > 2:
        n = sys.argv[3] if len(sys.argv) > 3 else 10
        for e in search_emails(sys.argv[2], n=int(n)):
            print(f"[{e['id']}]  {e.get('Date','')[:20]}")
            print(f"  From: {e.get('From','')}")
            print(f"  Subj: {e.get('Subject','')}")
            print(f"  {e.get('snippet','')[:100]}")
            print()

    elif cmd == 'email' and len(sys.argv) > 2:
        e = get_email(sys.argv[2])
        for k in ('From','To','Date','Subject'):
            print(f"{k}: {e.get(k,'')}")
        print("\n" + e.get('body','')[:3000])

    elif cmd == 'thread' and len(sys.argv) > 2:
        msgs = get_thread(sys.argv[2])
        for i, e in enumerate(msgs, 1):
            print(f"\n── Message {i} ──")
            for k in ('From','To','Date','Subject'):
                print(f"{k}: {e.get(k,'')}")
            print(e.get('body','')[:1000])

    elif cmd == 'send' and len(sys.argv) > 4:
        print(send_email(sys.argv[2], sys.argv[3], sys.argv[4]))

    elif cmd == 'reply' and len(sys.argv) > 3:
        print(reply_email(sys.argv[2], ' '.join(sys.argv[3:])))

    elif cmd == 'trash_email' and len(sys.argv) > 2:
        print(trash_email(sys.argv[2]))

    elif cmd == 'mark_read' and len(sys.argv) > 2:
        print(mark_read(sys.argv[2]))

    elif cmd == 'mark_unread' and len(sys.argv) > 2:
        print(mark_unread(sys.argv[2]))

    elif cmd == 'list' and len(sys.argv) > 2:
        for f in list_folder(sys.argv[2]):
            size = f.get('size','')
            print(f"  [{f['id']}]  {f['name']}  ({f['mimeType'].split('.')[-1]})  {size}")

    elif cmd == 'list_date' and len(sys.argv) > 3:
        for f in list_folder_by_date(sys.argv[2], sys.argv[3]):
            print(f"  {f['name']}  |  {f['createdTime'][:10]}  |  {f.get('webViewLink','')}")

    elif cmd == 'recent':
        n = sys.argv[2] if len(sys.argv) > 2 else 20
        for f in recent_files(n=int(n)):
            print(f"  [{f['id']}]  {f['name']}  {f.get('modifiedTime','')[:10]}  {f.get('webViewLink','')}")

    elif cmd == 'read' and len(sys.argv) > 2:
        print(read_doc(sys.argv[2]))

    elif cmd == 'search' and len(sys.argv) > 2:
        for f in search_files(' '.join(sys.argv[2:])):
            print(f"  [{f['id']}]  {f['name']}  {f.get('modifiedTime','')[:10]}")

    elif cmd == 'info' and len(sys.argv) > 2:
        print(json.dumps(file_info(sys.argv[2]), indent=2, ensure_ascii=False))

    elif cmd == 'create_folder' and len(sys.argv) > 2:
        parent = sys.argv[3] if len(sys.argv) > 3 else None
        f = create_folder(sys.argv[2], parent)
        print(f"Created folder: {f['name']}  [{f['id']}]  {f.get('webViewLink','')}")

    elif cmd == 'create_doc' and len(sys.argv) > 2:
        parent = sys.argv[3] if len(sys.argv) > 3 else None
        f = create_doc(sys.argv[2], parent)
        print(f"Created doc: {f['name']}  [{f['id']}]  {f.get('webViewLink','')}")

    elif cmd == 'upload' and len(sys.argv) > 2:
        parent = sys.argv[3] if len(sys.argv) > 3 else None
        f = upload_file(sys.argv[2], parent)
        print(f"Uploaded: {f['name']}  [{f['id']}]  {f.get('webViewLink','')}")

    elif cmd == 'download' and len(sys.argv) > 3:
        path = download_file(sys.argv[2], sys.argv[3])
        print(f"Downloaded to: {path}")

    elif cmd == 'move' and len(sys.argv) > 3:
        f = move_file(sys.argv[2], sys.argv[3])
        print(f"Moved: {f['name']}  [{f['id']}]")

    elif cmd == 'rename' and len(sys.argv) > 3:
        f = rename_file(sys.argv[2], sys.argv[3])
        print(f"Renamed to: {f['name']}  [{f['id']}]")

    elif cmd == 'trash_file' and len(sys.argv) > 2:
        print(trash_file(sys.argv[2]))

    elif cmd == 'share' and len(sys.argv) > 3:
        role = sys.argv[4] if len(sys.argv) > 4 else 'reader'
        print(share_file(sys.argv[2], sys.argv[3], role))

    else:
        print(__doc__)
