# utils/gmail_oauth.py
import pickle
from google.auth.transport.requests import Request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

TOKEN_FILE = "token.pickle"
USER_EMAIL = "marialynmirabel20@gmail.com"  # must match the account you used for OAuth

def get_access_token():
    with open(TOKEN_FILE, "rb") as token_file:
        creds = pickle.load(token_file)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as token_file:
            pickle.dump(creds, token_file)
    return creds.token

def send_oauth_email(to_email, subject, text_content, html_content=None, reply_to=None):
    access_token = get_access_token()

    # Create MIME message (text + html)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = USER_EMAIL
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = reply_to

    part1 = MIMEText(text_content, "plain")
    msg.attach(part1)

    if html_content:
        part2 = MIMEText(html_content, "html")
        msg.attach(part2)

    # XOAUTH2 authentication string
    auth_string = f"user={USER_EMAIL}\1auth=Bearer {access_token}\1\1"
    auth_string = base64.b64encode(auth_string.encode("ascii")).decode("ascii")

    # Connect and send
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    code, response = server.docmd("AUTH", "XOAUTH2 " + auth_string)
    if code != 235:
        raise Exception(f"Authentication failed: {code} {response}")

    server.sendmail(USER_EMAIL, to_email, msg.as_string())
    server.quit()
