from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import os

# --- Configuration ---
LOGIN_URL = "https://www.himalayanuniversity.com/student/student_login.php"
EXPECTED_URL = "https://www.himalayanuniversity.com/student/index.php"

# HTML Element IDs
USERNAME_FIELD_ID = "frm_registration_no"
PASSWORD_FIELD_ID = "frm_dob"
LOGIN_BUTTON_ID = "div_load"

# Telegram Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(subject: str, message: str):
    """Send a Telegram message via Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram token or Chat ID missing. Skipping notification.")
        return

    text = f"<b>{subject}</b>\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"✅ Telegram notification sent for: {subject}")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

def check_single_login(username, password, label):
    """Performs a single login check for a given user."""
    print(f"\n--- Starting Login Check for: {label} ---")
    
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # -----------------------------------------------------
    # FIX: Restore this line. It is required for GitHub Actions.
    options.add_argument("--remote-debugging-port=9222")
    # -----------------------------------------------------

    # Optional: these often help with stability in CI
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")

    service = Service(ChromeDriverManager().install())
    
    # Initialize driver
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"❌ Failed to initialize Driver for {label}: {e}")
        # Return False immediately if driver fails to start
        return False

    wait = WebDriverWait(driver, 15)

    status = "Failed"
    try:
        driver.get(LOGIN_URL)
        print(f"Opened {LOGIN_URL}")

        wait.until(EC.visibility_of_element_located((By.ID, USERNAME_FIELD_ID)))\
            .send_keys(username)
        print("Entered username")

        wait.until(EC.visibility_of_element_located((By.ID, PASSWORD_FIELD_ID)))\
            .send_keys(password)
        print("Entered password")

        wait.until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID))).click()
        print("Clicked login button")

        try:
            wait.until(EC.url_to_be(EXPECTED_URL))
            msg = f"Login succeeded for {label} at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            print(msg)
            send_telegram(f"{label}: Success ✅", msg)
            status = "Success"
        except TimeoutException:
            msg = f"Login failed for {label}: did not redirect to expected URL."
            print(msg)
            send_telegram(f"{label}: Failure ⚠️", msg)

    except Exception as e:
        msg = f"Error checking {label}: {str(e)}"
        print(msg)
        send_telegram(f"{label}: Error ❌", msg)
    finally:
        driver.quit()
        print(f"Finished check for {label}")
    
    return status == "Success"

def main():
    # Define your accounts here based on Env Vars
    # You can add as many as you need
    accounts = [
        {
            "user": os.getenv("LOGIN_USERNAME_1"),
            "pass": os.getenv("LOGIN_PASSWORD_1"),
            "label": os.getenv("LOGIN_LABEL_1", "Account 1")
        },
        {
            "user": os.getenv("LOGIN_USERNAME_2"),
            "pass": os.getenv("LOGIN_PASSWORD_2"),
            "label": os.getenv("LOGIN_LABEL_2", "Account 2")
        },
        {
            "user": os.getenv("LOGIN_USERNAME_3"),
            "pass": os.getenv("LOGIN_PASSWORD_3"),
            "label": os.getenv("LOGIN_LABEL_3", "Account 3")
        }
    ]

    results = []
    for acc in accounts:
        if acc["user"] and acc["pass"]:
            success = check_single_login(acc["user"], acc["pass"], acc["label"])
            results.append(success)
        else:
            print(f"Skipping {acc['label']} (credentials missing)")

    # Exit with error if ANY login failed (optional)
    if not all(results) and results:
        print("One or more login checks failed.")
        # exit(1) # Uncomment if you want the GitHub Action to appear red on failure

if __name__ == "__main__":
    main()