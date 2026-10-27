# Personal account setup

Chat integrations and the local FastAPI app are separate. A connection in chat does not authorize the local app. Open My accounts in `/dashboard` for the features below.

## GitHub

Enter your username and select Preview public GitHub projects. This uses GitHub's public REST API without a token. It shows up to 100 recently updated repositories, excluding archived projects, and labels forks. It does not access private code, verify ownership, change the resume, or infer proficiency. Save profile links to retain the username locally. The public API is rate limited.

Official reference: https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user

## LinkedIn

Save your profile URL and open it from the dashboard. This is a profile link, not a signed-in LinkedIn connection. Standard OpenID Connect sign-in exposes basic identity, not a full employment history or job-search feed. Use your own resume PDF in the upload workflow for work experience. No LinkedIn scraping or account automation is implemented.

Official reference: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2

## Gmail: one-time local authorization

1. Open https://console.cloud.google.com/ and create/select a project.
2. Enable Gmail API. Configure the Google Auth Platform consent screen. For a personal Gmail account, use an External app in Testing and add your email as a test user. Review Google's applicable terms yourself.
3. Create an OAuth client of type Desktop app. Download its JSON. Create a `.local` directory inside this repo and save the file as `.local/gmail-client.json`. Do not paste credentials into chat or commit them.
4. In PowerShell, from the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-integrations.txt
.\.venv\Scripts\python.exe scripts/connect_gmail.py
```

5. Complete sign-in and consent in your browser. The script uses Google's OAuth library with a loopback callback and saves `.local/gmail-token.json`.
6. In Gmail, create a `job-search` label and apply it to correspondence you want to view. Refresh the dashboard and select Read matching email headers. The default query is `label:job-search newer_than:90d`; edit it if your label differs.

The OAuth permission is `gmail.readonly`, which is mailbox-wide. The label/query limits this app's requests, not the permission granted by Google. A search reads at most 20 messages' subjects, senders, and dates. It does not fetch message bodies, send messages, or change tracker statuses. You can explicitly save a reviewed header and Gmail link to one role's timeline; that metadata is then stored in PostgreSQL and included in backups. Repeated saves to the same role are deduplicated. Read results and update the tracker status yourself. Search results are previews, not automatic recruitment-event classification. The saved header records what you confirmed in the preview; it is not cryptographically authenticated evidence of correspondence.

Tokens are plaintext local files protected by your OS account and excluded from Git, not an encrypted multi-user credential vault. Keep the API bound to 127.0.0.1. This integration is for a local personal workspace, not public hosting. The dashboard reports file presence separately from verified access; only a successful search verifies current authorization. Testing-mode authorizations can expire.

To disconnect, revoke access in your Google Account third-party connections and remove the local token file yourself. Clearing profile links does not revoke Gmail authorization. Never commit `.local` or expose its contents.

Official setup: https://developers.google.com/workspace/gmail/api/quickstart/python
Permissions: https://developers.google.com/workspace/gmail/api/auth/scopes
Search API: https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list

## Verification limits

Automated tests use mocked provider responses and check validation, metadata handling, missing authorization, and provider failures. The user completed local Gmail authorization, and a request through the running app returned HTTP 200 on 2026-10-27. The default job-search query returned zero headers; displaying and saving a real message reference has not yet been verified. Public GitHub requests do not constitute authenticated account access. Browser layout remains unverified.
