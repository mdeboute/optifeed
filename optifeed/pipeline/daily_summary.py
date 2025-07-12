import base64
import html
import os.path
import re
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from optifeed.utils.config import GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES, GMAIL_TOKEN_FILE
from optifeed.utils.llm import ask_something
from optifeed.utils.logger import logger
from optifeed.utils.rabbitmq import publish_task


def authenticate():
    """Authenticate with Gmail API and return credentials."""
    logger.info("🔐 Authenticating with Gmail...")
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    logger.info("✅ Gmail authentication successful.")
    return creds


class GmailApi:
    """Helper class to interact with Gmail API."""

    def __init__(self):
        creds = authenticate()
        self.service = build("gmail", "v1", credentials=creds)

    def find_emails(self, sender: str) -> List[dict]:
        """Fetch unread emails from a specific sender."""
        logger.info("📥 Fetching matching emails...")
        request = (
            self.service.users()
            .messages()
            .list(userId="me", q=f"from:{sender} is:unread", maxResults=200)
        )
        try:
            result = request.execute()
            messages = result.get("messages", [])
            logger.info(f"✅ Found {len(messages)} unread matching emails.")
            return messages
        except HttpError as e:
            logger.error(f"❌ Failed to fetch emails: {e}")
            return []

    def get_email(self, email_id: str) -> str:
        """Retrieve and decode the content of an email by its ID."""
        try:
            request = (
                self.service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
            )
            result = request.execute()

            payload = result["payload"]
            parts = payload.get("parts", [])
            data = ""

            for part in parts:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data")
                    break

            if not data and "body" in payload:
                data = payload["body"].get("data", "")

            decoded = base64.urlsafe_b64decode(data).decode("utf-8")
            return decoded

        except Exception as e:
            logger.error(f"❌ Error while decoding email {email_id}: {e}")
            return ""

    def mark_as_read(self, email_ids: List[str]):
        """Mark the given email IDs as read in Gmail."""
        if not email_ids:
            return
        logger.info(f"📬 Marking {len(email_ids)} emails as read...")
        try:
            self.service.users().messages().batchModify(
                userId="me", body={"ids": email_ids, "removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info("✅ Emails marked as read.")
        except HttpError as e:
            logger.error(f"❌ Failed to mark emails as read: {e}")


def clean_email_content(raw: str) -> str:
    """Clean and sanitize raw email text before summarization."""
    text = re.sub(r"https?://\S+", "", raw)
    text = re.sub(r"Se desinscrire.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Tous droits reserves.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[-_]{3,}", "\n", text)
    text = text.replace("\r", "")
    text = re.sub(r"\n{2,}", "\n\n", text)
    return html.unescape(text.strip())


def summarize_emails_with_gemini(contents: str) -> str:
    """Generate a daily digest summary using Gemini based on email contents."""
    prompt = f"""
    Generate a concise daily digest in French based on raw newsletter content below.
    Instructions:
    - Start with a friendly greeting
    - Use section titles
    - Format lists with "-"
    - No code blocks or hyperlinks
    - Use emojis for tone, but keep it natural
    - Keep it brief and engaging
    - End with a positive sign-off
    - Don't include any commercial offers or promotions
    Raw content:
    {contents}
    """
    try:
        response = ask_something(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        return "❌ Could not generate summary."


def main():
    client = GmailApi()

    sender = "team@aktionnaire.com OR placement@news.meilleurtaux.com OR daily@timetosignoff.fr"
    emails = client.find_emails(sender)

    if not emails:
        logger.info("📭 No new emails to summarize today.")
        return

    email_ids = [email["id"] for email in emails]
    raw_contents = [client.get_email(email_id) for email_id in email_ids]
    cleaned_contents = [clean_email_content(c) for c in raw_contents if c.strip()]
    full_content = "\n\n".join(cleaned_contents)

    summary = summarize_emails_with_gemini(full_content)

    publish_task(
        {
            "type": "alert",
            "message": f"📅 Daily Summary:\n\n{summary}",
        }
    )

    client.mark_as_read(email_ids)


if __name__ == "__main__":
    main()
