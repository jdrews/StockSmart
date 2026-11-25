import os
import re
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

# Micro Center store IDs to watch, comma-separated. Default: 131 (Dallas
# store). See README for how to find your stores' IDs.
STORE_IDS = os.getenv("STORE_IDS", "")

# Deprecated single-store alias, kept so existing config files keep working.
# Ignored when STORE_IDS is set.
STORE_ID = os.getenv("STORE_ID", "")

# Product page URL to watch
PRODUCT_URL = os.getenv(
    "PRODUCT_URL",
    "https://www.microcenter.com/product/687907/amd-ryzen-7-9800x3d-granite-ridge-am5-470ghz-8-core-boxed-processor-heatsink-not-included",
)

# Seconds between stock checks
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "120"))

# Seconds between the per-store page fetches inside one check. Each store is a
# separate request, so more stores means more requests per poll - keep the
# total request rate polite to avoid Cloudflare challenges.
STORE_CHECK_DELAY = int(os.getenv("STORE_CHECK_DELAY", "5"))

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

def parse_store_ids():
    # Build the store list from STORE_IDS, falling back to the deprecated
    # STORE_ID alias and then to the built-in default. Micro Center pads store
    # numbers to three digits (65 -> 065), so ids are normalized for matching
    # and for display. Raises ValueError on anything non-numeric.
    raw = STORE_IDS or STORE_ID or "131"

    store_ids = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(
                f"Invalid store ID {part!r} - store IDs must be digits only, e.g. STORE_IDS=131,145"
            )
        store_id = part.zfill(3)
        if store_id not in store_ids:
            store_ids.append(store_id)

    if not store_ids:
        raise ValueError("No store IDs configured - set STORE_IDS in config.env, e.g. STORE_IDS=131,145")
    return store_ids

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

def send_ntfy(message, click_url=None):
    # Push the alert to your phone via ntfy.sh (see README for setup)
    try:
        response = requests.post(
            f"{NTFY_URL.rstrip('/')}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": "Micro Center Stock Alert",
                "Priority": "high",
                "Tags": "rotating_light",
                # Tapping the notification opens the product page at the
                # in-stock store
                "Click": click_url or PRODUCT_URL,
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

def notify(subject, body, click_url=None):
    # Deliver the alert through every configured channel (ntfy push, optional
    # email). Falls back to the console if no channel is configured or every
    # send fails.
    delivered = False
    if NTFY_TOPIC:
        delivered = send_ntfy(f"{subject}\n{body}", click_url) or delivered
    if EMAIL_ENABLED:
        delivered = send_email(subject, body) or delivered
    if not delivered:
        print(f"[No notification delivered - console only] {subject}: {body}")
    return delivered

def store_label(page, store_id):
    # Read the store's city and state from the store picker in the page, so the
    # alert can say which store has stock. This is cosmetic: any miss falls
    # back to the bare store ID, so a Micro Center markup change can never
    # block an alert.
    match = re.search(
        rf'store_{store_id}"[^>]*>.*?storeState">([^<]*)<.*?storeName">([^<]*)<',
        page,
        re.S,
    )
    if match:
        state = match.group(1).strip()
        city = match.group(2).strip()
        if city and state:
            return f"{city}, {state} ({store_id})"
    return f"Store {store_id}"

def check_store(store_id):
    # Fetch the product page as a normal browser request and read the stock
    # status for one store from the embedded page data. The storeSelected
    # cookie selects the store, so each store needs its own request.
    # Returns ("in" | "out" | "blocked", label); "blocked" means Cloudflare
    # answered instead of the product page.
    response = requests.get(
        PRODUCT_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        cookies={"storeSelected": store_id},
        timeout=30,
    )
    response.raise_for_status()
    page = response.text

    # Distinguish a Cloudflare block from a genuine "Out of Stock"
    if "Attention Required" in page or "cf-chl" in page:
        print(f"Warning: Cloudflare challenge page received for store {store_id} - skipping this store.")
        return "blocked", f"Store {store_id}"

    label = store_label(page, store_id)

    # Search for 'inStock':'True' in the page source
    if "'inStock':'True'" in page:
        print(f"In Stock! {label}")
        return "in", label
    print(f"Out of Stock! {label}")
    return "out", label

def check_all_stores(store_ids):
    # Check every configured store (one page fetch each) and return the
    # (store_id, label) pairs that are in stock. A Cloudflare block on one
    # store skips that store only; the rest of the poll continues.
    in_stock = []
    for index, store_id in enumerate(store_ids):
        status, label = check_store(store_id)
        if status == "in":
            in_stock.append((store_id, label))
        if index < len(store_ids) - 1:
            time.sleep(STORE_CHECK_DELAY)  # Be polite between page fetches
    return in_stock

def stock_alert(in_stock):
    # Build the one alert that lists every store found in stock. Returns the
    # subject, body, and the URL the push notification opens.
    labels = [label for _, label in in_stock]
    if len(labels) == 1:
        subject = f"In Stock! {labels[0]}"
    else:
        subject = f"In Stock! {len(labels)} stores"

    body = "Your Micro Center product is now in stock at:\n"
    body += "".join(f"  - {label}\n" for label in labels)
    body += "Reserve it online or head to the store to get it while supplies last."

    # Opens the product page at the first in-stock store
    click_url = f"{PRODUCT_URL}?storeid={in_stock[0][0]}"
    return subject, body, click_url

def main():
    # Validate the store list before doing anything else
    try:
        store_ids = parse_store_ids()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

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

    print(f"Watching {len(store_ids)} store(s): {', '.join(store_ids)}")

    while True:
        try:
            # One alert naming every in-stock store, then done
            in_stock = check_all_stores(store_ids)
            if in_stock:
                subject, body, click_url = stock_alert(in_stock)
                notify(subject, body, click_url)
                sys.exit()  # Notified; done watching
        except Exception as e:
            print(f"Stock check failed: {e}")
        time.sleep(POLL_INTERVAL)  # Seconds between stock checks (see POLL_INTERVAL in config.env)

if __name__ == "__main__":
    main()
