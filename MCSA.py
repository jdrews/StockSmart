import os
import sys
import time
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load configuration. .venv/config.env takes precedence over the repo-root
# config.env, so keep machine-specific values (like email credentials) in
# .venv/config.env where they won't be committed to git.
load_dotenv("config.env")
load_dotenv(".venv/config.env", override=True)

# --- Configuration (override via config.env) ---

# Micro Center store ID. Default: 131 (Dallas store). See README for how to
# find your store's ID.
STORE_ID = os.getenv("STORE_ID", "131")

# Product page URL to watch
PRODUCT_URL = os.getenv(
    "PRODUCT_URL",
    "https://www.microcenter.com/product/687907/amd-ryzen-7-9800x3d-granite-ridge-am5-470ghz-8-core-boxed-processor-heatsink-not-included",
)

# Seconds between stock checks
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "120"))

# ntfy.sh push notifications (recommended channel - see README for setup)
NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")

# Optional: legacy Gmail SMTP email channel
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").strip().lower() in ("1", "true", "yes")

# Browser User-Agent for the product page request. Micro Center's Cloudflare
# protection challenges headless browsers, while plain HTTP requests with a
# normal browser User-Agent pass through.
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)

def prompt():
    # Prompts the user for email and password securely (only used when the
    # email channel is enabled)
    print("Security Disclaimer:\n"
          "Your personal information can only be accessed by a system administrator while the program is running.\n"
          "This information cannot be accessed by outside users and is immediately deleted upon the end of program runtime.\n"
          "This means that you will have to re-enter your information every time the program is ran.\n"
          "\n"
          "Email Information Instructions:\n"
          "Go to myaccount.google.com, search 'App Passwords', and click the respective option.\n"
          "In the 'App name' field enter any title specific to this program.\n"
          "Copy and paste the newly generated password into the appropriate field below:")

    # Set the environment variables
    os.environ["email"] = input("Enter your email: ")
    os.environ["password"] = input("Enter your password: ")

def send_ntfy(message):
    # Push the alert to your phone via ntfy.sh (see README for setup)
    try:
        response = requests.post(
            f"{NTFY_URL.rstrip('/')}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": "Micro Center Stock Alert",
                "Priority": "high",
                "Tags": "rotating_light",
                "Click": PRODUCT_URL,  # Tapping the notification opens the product page
            },
            timeout=15,
        )
        response.raise_for_status()
        print("ntfy notification sent!")
        return True
    except Exception as e:
        print(f"Failed to send ntfy notification: {e}")
        return False

def send_email(subject, body):
    try:
        # Get the environment variables
        email_user = os.getenv("email")
        email_password = os.getenv("password")

        # Confirm whether email credentials were entered
        if not email_user or not email_password:
            raise Exception("Email credentials not found")

        # Set up the email
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_user
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the email server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.sendmail(email_user, email_user, msg.as_string())

        print("Email sent successfully!")
        return True
    # Email exception
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def test_email():
    # Send a test email to confirm the email channel is working
    send_email(
        'Test Email Successful',
        'This is a test email to confirm that your email login is correctly working alongside SMTP within the Microcenter Stock Python Application.\n\n'
        'You may now let the application run in the background while it actively checks stock of your selected Microcenter product.',
    )

def notify(subject, body):
    # Deliver the alert through every configured channel (ntfy push, optional
    # email). Falls back to the console if no channel is configured or every
    # send fails.
    delivered = False
    if NTFY_TOPIC:
        delivered = send_ntfy(f"{subject}\n{body}") or delivered
    if EMAIL_ENABLED:
        delivered = send_email(subject, body) or delivered
    if not delivered:
        print(f"[No notification delivered - console only] {subject}: {body}")
    return delivered

def check_stock():
    # Fetch the product page as a normal browser request and read the stock
    # status for the selected store from the embedded page data.
    response = requests.get(
        PRODUCT_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        cookies={"storeSelected": STORE_ID},
        timeout=30,
    )
    response.raise_for_status()
    page = response.text

    # Distinguish a Cloudflare block from a genuine "Out of Stock"
    if "Attention Required" in page or "cf-chl" in page:
        print("Warning: Cloudflare challenge page received - skipping this check.")
        return False

    # Search for 'inStock':'True' in the page source
    if "'inStock':'True'" in page:
        print("In Stock!")
        notify(
            "In Stock!",
            "Your Micro Center product is now in stock. Reserve it online or head to the store to get it while supplies last.",
        )
        return True
    print("Out of Stock!")
    return False

def main():
    # Enter email and password (only needed when the email channel is enabled)
    if EMAIL_ENABLED:
        prompt()

        # Test email
        test_email()

    # Sanity-check the notification configuration
    if not NTFY_TOPIC and not EMAIL_ENABLED:
        print("Warning: no notification channel configured.")
        print("Set NTFY_TOPIC in config.env for phone push notifications (recommended).")
        print("Alerts will only be printed to the console.")

    while True:
        try:
            if check_stock():
                sys.exit()  # Notified; done watching
        except Exception as e:
            print(f"Stock check failed: {e}")
        time.sleep(POLL_INTERVAL)  # Seconds between stock checks (see POLL_INTERVAL in config.env)

if __name__ == "__main__":
    main()
