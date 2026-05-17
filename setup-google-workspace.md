# /setup-google-workspace

Interactive setup wizard for the Google Workspace skill (Gmail + Drive access for Claude Code).
Does everything automatically where possible. Only asks the user for steps that require manual action.

## Instructions

Run through the following steps in order. At each step, do what you can automatically using Bash, then pause and ask the user only when human action is genuinely required.

---

### STEP 1 — Detect environment

Run these automatically:
```bash
echo $USERNAME
py --version 2>&1
```

Greet the user: "מתחיל הגדרה של Google Workspace Skill. אעשה כל מה שאפשר אוטומטית."

Report: Python version found (or not found). If Python is missing, tell the user to install it from python.org and stop.

---

### STEP 2 — Install Python packages

Run automatically:
```bash
py -m pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client 2>&1 | tail -5
```

Report success or any errors.

---

### STEP 3 — Find downloaded files

Ask the user:
> "איפה שמרת את קבצי ה-setup שקיבלת? (gdrive.py ו-google-workspace.md)
> תדביק את הנתיב לתיקייה, למשל: C:\Users\שם\Downloads\google-workspace-skill"

Wait for their answer. Store the path as SOURCE_DIR.

Check that both files exist there:
```bash
ls "<SOURCE_DIR>/gdrive.py" 2>&1
ls "<SOURCE_DIR>/google-workspace.md" 2>&1
```

If missing, tell the user which file is missing and ask them to check.

---

### STEP 4 — Set up ~/.claude directory

Run automatically using the detected USERNAME:

1. Create `C:\Users\<USERNAME>\.claude\commands\` if it doesn't exist:
```bash
mkdir -p "/c/Users/$USERNAME/.claude/commands"
```

2. Copy gdrive.py:
```bash
cp "<SOURCE_DIR>/gdrive.py" "/c/Users/$USERNAME/.claude/gdrive.py"
```

3. Update the hardcoded paths inside gdrive.py to match this user's USERNAME:
   - Read the file
   - Replace any occurrence of the old username (from whatever is there) with the actual USERNAME in the CLIENT_SECRET and TOKEN_FILE lines
   - Write the file back

4. Copy the skill file:
```bash
cp "<SOURCE_DIR>/google-workspace.md" "/c/Users/$USERNAME/.claude/commands/google-workspace.md"
```

5. Update paths inside google-workspace.md — replace all occurrences of the old username with USERNAME.

Report: "העתקתי את הקבצים ועדכנתי את הנתיבים."

---

### STEP 5 — Google Cloud setup (manual — can't be automated)

Tell the user:
> "עכשיו צריך ליצור credentials ב-Google Cloud. זה לוקח ~10 דקות ועושים את זה פעם אחת בלבד.
> פתחו את console.cloud.google.com ועקבו אחרי השלבים:"

Print these steps clearly and numbered:
1. לחצו **New Project** (שם לבחירתכם) ← **Create**
2. בתפריט הצד: **APIs & Services → Library**
   - חפשו **Google Drive API** ← Enable
   - חפשו **Gmail API** ← Enable
3. **APIs & Services → OAuth consent screen** ← External ← מלאו שם ← שמרו
   - בלשונית **Test users** ← הוסיפו את כתובת המייל שלכם
4. **APIs & Services → Credentials** ← **Create Credentials → OAuth client ID**
   - Application type: **Desktop app** ← Create
5. לחצו **Download JSON** על ה-credential שנוצר

Then ask:
> "סיימתם? אחרי שהורדתם את קובץ ה-JSON, שנו את שמו ל-`client secret.json` ושמרו אותו ב:
> `C:\Users\<USERNAME>\.claude\client secret.json`
>
> כשסיימתם כתבו 'מוכן'"

Wait for the user to confirm.

---

### STEP 6 — Verify client secret exists

Run automatically:
```bash
ls "/c/Users/$USERNAME/.claude/client secret.json" 2>&1
```

If missing — tell the user the exact path again and wait. Re-check after they confirm.

---

### STEP 7 — First authentication

Tell the user:
> "עכשיו אריץ את האימות הראשוני. יפתח דפדפן — בחרו את חשבון ה-Gmail שלכם ואשרו את ההרשאות."

Run:
```bash
py "/c/Users/$USERNAME/.claude/gdrive.py" emails 2>&1
```

**What the user will see in the browser:**
- בחירת חשבון Google
- מסך "Google hasn't verified this app" → לחצו **Advanced → Go to app**
- אשרו את כל ההרשאות → **Allow**

After the command returns, check if it printed email subjects (success) or an error.

If success — celebrate: "✅ הכל עובד! drive_token.json נוצר."

If error — diagnose and help fix.

---

### STEP 8 — Final verification

Run a quick test automatically:
```bash
py "/c/Users/$USERNAME/.claude/gdrive.py" emails 2 2>&1
```

If it returns 2 emails — setup is complete.

Tell the user:
> "🎉 ההגדרה הושלמה בהצלחה!
>
> כעת תוכלו להשתמש ב-/google-workspace בכל שיחה ב-Claude Code.
> פשוט כתבו בקשות כמו:
> - 'תראה לי את המיילים האחרונים שלי'
> - 'חפש בדרייב שלי קבצים על...'
> - 'שלח מייל ל-X עם הנושא Y'"
