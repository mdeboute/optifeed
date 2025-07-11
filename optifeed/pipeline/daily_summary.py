import os.path
from math import log

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from optifeed.api.app import publish_task
from optifeed.utils.config import (
    GMAIL_CREDENTIALS_FILE,
    GMAIL_TOKEN_FILE,
    SCOPES,
    TELEGRAM_CHAT_ID,
    model,
)
from optifeed.utils.logger import logger


def get_gmail_service():
    """
    Authenticate and return the Gmail API service.
    """
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def fetch_latest_emails(service, query):
    """
    Fetch latest emails matching the given query and mark them as read.
    """
    try:
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=3)
            .execute()
        )
        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            msg_data = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="full")
                .execute()
            )
            headers = msg_data["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            from_ = next((h["value"] for h in headers if h["name"] == "From"), "")
            snippet = msg_data.get("snippet", "")
            body = ""
            parts = msg_data["payload"].get("parts", [])
            if parts:
                for part in parts:
                    if part["mimeType"] == "text/plain":
                        body += part["body"].get("data", "")
            else:
                body += msg_data["payload"]["body"].get("data", "")

            emails.append(
                {
                    "id": msg["id"],
                    "from": from_,
                    "subject": subject,
                    "snippet": snippet,
                    "body": body,
                }
            )

            # Mark email as read
            service.users().messages().modify(
                userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}
            ).execute()

        return emails

    except HttpError as error:
        logger.error(f"❌ An error occurred: {error}")
        return []


def summarize_emails_with_gemini(emails, model):
    """
    Use Gemini to create a short daily summary from email contents.
    """
    content = ""
    for email in emails:
        content += f"\n=== FROM: {email['from']} ===\nSUBJECT: {email['subject']}\nBODY: {email['body']}\n"

    prompt = f"""
    You are an assistant reading newsletters.
    Your task is to generate a short daily digest in French.
    Focus on key news, trends, or investment insights. Keep it clear and concise.
    Your output will be sent to a Telegram channel, so you must write it in a cool and engaging way with markdown formatting (no codeblock), emojis and be concise.

    Here is the raw content from the emails:

    {content}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        return "❌ Could not generate summary."


def main():
    service = get_gmail_service()

    # Query for emails from the specific senders
    query = "from:(team@aktionnaire.com OR placement@news.meilleurtaux.com OR daily@timetosignoff.fr) is:unread"
    emails = fetch_latest_emails(service, query)
    logger.info(f"📨 Fetched {len(emails)} matching emails.")

    if emails:
        summary = summarize_emails_with_gemini(emails, model)
        publish_task(
            {
                "type": "alert",
                "message": f"📅 Daily Summary:\n\n{summary}",
            }
        )
    else:
        logger.info("📭 No new emails to summarize today.")


if __name__ == "__main__":
    main()
