"""Authorize a personal local workspace; the user completes Google consent."""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'
SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'


if __name__ == '__main__':
    LOCAL.mkdir(exist_ok=True)
    client_file = LOCAL / 'gmail-client.json'
    if not client_file.exists():
        raise SystemExit('Missing .local/gmail-client.json. Follow docs/INTEGRATIONS.md to create a Desktop OAuth client.')
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes=[SCOPE])
    credentials = flow.run_local_server(host='localhost', port=0, access_type='offline',
                                        prompt='consent', authorization_prompt_message='Complete authorization in the browser.')
    (LOCAL / 'gmail-token.json').write_text(credentials.to_json(), encoding='utf-8')
    print('Gmail authorized locally. Refresh the dashboard and explicitly search your job-search label.')
