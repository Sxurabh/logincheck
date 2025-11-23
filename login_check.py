from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import os
import urllib3
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── Configuration ─────────────────────────────────────────────────────────────
LOGIN_URL       = "https://www.himalayanuniversity.com/student/student_login.php"
DASHBOARD_URL   = "https://www.himalayanuniversity.com/student/index.php"
RESULT_PAGE_URL = "https://www.himalayanuniversity.com/student/student_campus_result.php"

# HTML Element IDs
USERNAME_FIELD_ID = "frm_registration_no"
PASSWORD_FIELD_ID = "frm_dob"
LOGIN_BUTTON_ID   = "div_load"

# Telegram Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message: str):
    """Send a Telegram message via Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def get_driver():
    """Initializes and returns a configured Chrome Driver (Local or CI)."""
    options = Options()
    
    ci_binary_path = "/usr/bin/chromium-browser"
    is_ci_env = os.path.exists(ci_binary_path)

    if is_ci_env:
        print("🔧 Configuring for GitHub Actions (Headless Linux)...")
        options.binary_location = ci_binary_path
        options.add_argument("--headless=new") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
    else:
        print("💻 Configuring for Local Machine (Visible UI)...")
        # options.add_argument("--headless=new") # Uncomment to hide browser locally
        pass

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    
    # Anti-Blocking
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def check_result_download(driver):
    """Checks if the result download link is reachable."""
    try:
        driver.get(RESULT_PAGE_URL)
        wait = WebDriverWait(driver, 15)
        
        # Locate 'Download' button
        download_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(text(), 'Download')]")
        ))
        
        # Extract href from parent <a>
        download_href = download_btn.find_element(By.XPATH, "./..").get_attribute("href")
        
        if not download_href:
            return False, "Link not found"

        # Check Link Health
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        r = requests.get(download_href, headers=headers, timeout=15, verify=False)
        
        if r.status_code == 200:
            return True, "Available ⬇️"
        elif r.status_code == 500:
            return False, "HTTP 500 (Server Error)"
        else:
            return False, f"HTTP {r.status_code}"

    except TimeoutException:
        return False, "Download button missing"
    except Exception as e:
        return False, f"Error: {str(e)[:30]}..." 

def process_account(driver, username, password, label):
    """Runs the login check for a single account using the shared driver."""
    print(f"\n🔹 Processing: {label}")
    
    driver.delete_all_cookies()
    wait = WebDriverWait(driver, 30)
    
    student_name = "Unknown User"
    
    try:
        # 1. Login
        driver.get(LOGIN_URL)
        wait.until(EC.visibility_of_element_located((By.ID, USERNAME_FIELD_ID))).send_keys(username)
        wait.until(EC.visibility_of_element_located((By.ID, PASSWORD_FIELD_ID))).send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID))).click()

        wait.until(EC.url_to_be(DASHBOARD_URL))
        
        # 2. Extract Name
        try:
            name_element = driver.find_element(By.CLASS_NAME, "log_txt")
            raw_text = name_element.text.strip()
            student_name = raw_text.split("Welcome")[-1].strip().title() if "Welcome" in raw_text else raw_text
        except Exception:
            pass 

        # 3. Check Result
        is_download_ok, result_msg = check_result_download(driver)

        # 4. Prepare Aesthetic Message
        timestamp = time.strftime('%d %b • %H:%M UTC')
        
        if is_download_ok:
            # ✅ SUCCESS TEMPLATE
            msg = (
                f"🎓 <b>{student_name}</b>\n"
                f"──────────────────────\n"
                f"🔐 <b>Login:</b> Verified ✅\n"
                f"📄 <b>Result:</b> {result_msg}\n"
                f"──────────────────────\n"
                f"🏷️ <i>{label}</i>\n"
                f"🕒 <i>{timestamp}</i>"
            )
        else:
            # ⚠️ ACTION REQUIRED TEMPLATE
            msg = (
                f"🚨 <b>ACTION REQUIRED</b>\n"
                f"<b>User:</b> {student_name}\n"
                f"──────────────────────\n"
                f"🔐 <b>Login:</b> Success\n"
                f"❌ <b>Result:</b> <b>{result_msg}</b>\n"
                f"──────────────────────\n"
                f"🏷️ <i>{label}</i>\n"
                f"🕒 <i>{timestamp}</i>"
            )

        send_telegram(msg)
        print(f"   ✅ Finished {label}: Login=OK, Result={result_msg}")
        return True

    except TimeoutException:
        print(f"   ❌ Timeout during login for {label}")
        
        # Capture context for the error
        current_page = driver.title if driver.title else "Unknown/Blank Page"
        current_url = driver.current_url if driver.current_url else "No URL"
        timestamp = time.strftime('%d %b • %H:%M UTC')

        # ⛔ FAILURE TEMPLATE
        msg = (
            f"⛔ <b>LOGIN FAILED</b>\n"
            f"──────────────────────\n"
            f"👤 <b>Account:</b> {label}\n"
            f"📉 <b>Reason:</b> Timeout / Elements not found\n"
            f"🔗 <b>Page:</b> {current_page}\n"
            f"──────────────────────\n"
            f"🕒 <i>{timestamp}</i>"
        )
        send_telegram(msg)
        return False

    except Exception as e:
        print(f"   ❌ Error for {label}: {e}")
        timestamp = time.strftime('%d %b • %H:%M UTC')
        
        msg = (
            f"💥 <b>SCRIPT CRASH</b>\n"
            f"──────────────────────\n"
            f"👤 <b>Account:</b> {label}\n"
            f"🐛 <b>Error:</b> {str(e)[:100]}\n"
            f"──────────────────────\n"
            f"🕒 <i>{timestamp}</i>"
        )
        send_telegram(msg)
        return False

def get_accounts_from_env():
    """Fetches LOGIN_USERNAME_X accounts from env vars."""
    accounts = []
    i = 1
    while True:
        user = os.getenv(f"LOGIN_USERNAME_{i}")
        pw = os.getenv(f"LOGIN_PASSWORD_{i}")
        lbl = os.getenv(f"LOGIN_LABEL_{i}", f"Account {i}")
        
        if not user or not pw:
            break
            
        accounts.append({"user": user, "pass": pw, "label": lbl})
        i += 1
    return accounts

def main():
    accounts = get_accounts_from_env()
    if not accounts:
        print("⚠️ No accounts found. Did you create a .env file?")
        return

    print(f"🚀 Starting checks for {len(accounts)} accounts...")
    
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(45)

        results = []
        for acc in accounts:
            success = process_account(driver, acc["user"], acc["pass"], acc["label"])
            results.append(success)
            
        if not all(results):
            print("⚠️ Some checks failed.")

    except Exception as e:
        print(f"🔥 Critical Driver Error: {e}")
    finally:
        if driver:
            driver.quit()
            print("🛑 Driver closed.")

if __name__ == "__main__":
    main()