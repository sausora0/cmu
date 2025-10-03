# generate_token.py
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://mail.google.com/"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"

def get_gmail_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return creds

if __name__ == "__main__":
    creds = get_gmail_credentials()
    print("✅ Token generated successfully!")
    print("Access Token:", creds.token)
