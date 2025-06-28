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

# Configuration variables
LOGIN_URL = "https://www.himalayanuniversity.com/student/student_login.php"
USERNAME = os.getenv("LOGIN_USERNAME")
PASSWORD = os.getenv("LOGIN_PASSWORD")
USERNAME_FIELD_ID = "frm_registration_no"
PASSWORD_FIELD_ID = "frm_dob"
LOGIN_BUTTON_ID = "div_load"
EXPECTED_URL = "https://www.himalayanuniversity.com/student/index.php"

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")  # must be a valid chat ID (e.g. -1001234567890 or your user ID)

def send_telegram(subject: str, message: str):
    """Send a Telegram message via Bot API, and log any error body."""
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
        print("✅ Telegram notification sent.")
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Telegram HTTP error: {http_err}")
        print("Response body:", resp.status_code, resp.text)
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

# --- Selenium setup ---
options = Options()
options.binary_location = "/usr/bin/chromium-browser"
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--remote-debugging-port=9222")

service = Service(ChromeDriverManager().install())
driver  = webdriver.Chrome(service=service, options=options)
wait    = WebDriverWait(driver, 10)

try:
    driver.get(LOGIN_URL)
    print(f"Opened {LOGIN_URL}")

    wait.until(EC.visibility_of_element_located((By.ID, USERNAME_FIELD_ID)))\
        .send_keys(USERNAME)
    print("Entered username")

    wait.until(EC.visibility_of_element_located((By.ID, PASSWORD_FIELD_ID)))\
        .send_keys(PASSWORD)
    print("Entered password")

    wait.until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID))).click()
    print("Clicked login button")

    try:
        wait.until(EC.url_to_be(EXPECTED_URL))
        success_msg = f"Login succeeded at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        print(success_msg)
        send_telegram("Login Success ✅", success_msg)
    except TimeoutException:
        error_msg = "Login failed: did not redirect to the expected URL in time."
        print(error_msg)
        send_telegram("Login Failure ⚠️", error_msg)

except TimeoutException:
    error_msg = "Timeout: Element not found or page too slow."
    print(error_msg)
    send_telegram("Login Failure ⚠️", error_msg)
except Exception as e:
    error_msg = f"Unexpected error: {e}"
    print(error_msg)
    send_telegram("Login Failure ⚠️", error_msg)
finally:
    driver.quit()
    print("Browser closed")
