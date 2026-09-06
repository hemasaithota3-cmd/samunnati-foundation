import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# 1. Load environment variables from .env file
load_dotenv()

# 2. Fetch configuration
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
ADMIN_NOTIFY_EMAIL = os.getenv("ADMIN_NOTIFY_EMAIL")

# 3. Create the test email message
msg = EmailMessage()
msg["Subject"] = "SMTP Test Email"
msg["From"] = MAIL_DEFAULT_SENDER
msg["To"] = ADMIN_NOTIFY_EMAIL
msg.set_content(
    "Hello!\n\nIf you are reading this, your SMTP environment settings are configured correctly."
)

# 4. Connect to the server and send the email
try:
    print(f"Connecting to {MAIL_SERVER}:{MAIL_PORT}...")
    
    # Standard connection setup for port 587 (STARTTLS)
    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
        if MAIL_USE_TLS:
            server.starttls()
            print("TLS connection established.")

        print(f"Authenticating as {MAIL_USERNAME}...")
        server.login(MAIL_USERNAME, MAIL_PASSWORD)

        print(f"Sending test email to {ADMIN_NOTIFY_EMAIL}...")
        server.send_message(msg)

    print("\nSuccess! Email sent without any errors.")

except Exception as e:
    print(f"\nFailed to send email. Error details:\n{e}")