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
import urllib3

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

def send_telegram(subject: str, message: str):
    """Send a Telegram message via Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        # Silent return if no config, to avoid log spam
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
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def get_driver():
    """Initializes and returns a configured Chrome Driver."""
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222") # Required for CI
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    
    # OPTIMIZATION: Disable images to speed up loading
    options.add_argument("--blink-settings=imagesEnabled=false") 
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def check_result_download(driver):
    """
    Checks if the result download link is reachable.
    """
    try:
        driver.get(RESULT_PAGE_URL)
        wait = WebDriverWait(driver, 8) # Reduced timeout for speed
        
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(download_href, headers=headers, timeout=10, verify=False)
        
        if r.status_code == 200:
            return True, "Available ✅"
        elif r.status_code == 500:
            return False, "⛔ <b>HTTP 500 Error</b> (Server Issue)"
        else:
            return False, f"⚠️ HTTP {r.status_code}"

    except TimeoutException:
        return False, "⚠️ Download button missing"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:50]}" # Truncate long errors

def process_account(driver, username, password, label):
    """
    Runs the login check for a single account using the shared driver.
    """
    print(f"\n🔹 Processing: {label}")
    
    # CLEANUP: Ensure clean session before login
    driver.delete_all_cookies()
    
    wait = WebDriverWait(driver, 15)
    login_success = False
    result_msg = "Skipped"
    is_download_ok = False
    student_name = "Unknown"

    try:
        # 1. Login
        driver.get(LOGIN_URL)
        wait.until(EC.visibility_of_element_located((By.ID, USERNAME_FIELD_ID))).send_keys(username)
        wait.until(EC.visibility_of_element_located((By.ID, PASSWORD_FIELD_ID))).send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID))).click()

        # Wait for Dashboard
        wait.until(EC.url_to_be(DASHBOARD_URL))
        login_success = True
        
        # 2. Extract Name (Optimized Extraction)
        try:
            name_element = driver.find_element(By.CLASS_NAME, "log_txt")
            raw_text = name_element.text.strip()
            # Simple split logic
            student_name = raw_text.split("Welcome")[-1].strip().title() if "Welcome" in raw_text else raw_text
        except Exception:
            pass # Name extraction is non-critical

        # 3. Check Result
        is_download_ok, result_msg = check_result_download(driver)

        # 4. Notify
        res_emoji = "✅" if is_download_ok else "❌"
        msg = (
            f"👤 <b>User: {student_name}</b>\n"
            f"✅ <b>Login:</b> Success\n"
            f"{res_emoji} <b>Result:</b> {result_msg}\n"
            f"🏷️ {label}\n"
            f"🕒 {time.strftime('%H:%M:%S UTC')}"
        )
        
        # Determine Alert Priority
        subject = f"{label}: Status Update"
        if not is_download_ok:
            subject = f"{label}: Action Required ⚠️"

        send_telegram(subject, msg)
        print(f"   ✅ Finished {label}: Login=OK, Result={result_msg}")
        return True

    except TimeoutException:
        print(f"   ❌ Timeout during login for {label}")
        send_telegram(f"{label}: Login Failed ❌", "Login timed out or redirection failed.")
        return False
    except Exception as e:
        print(f"   ❌ Error for {label}: {e}")
        send_telegram(f"{label}: Script Error ❌", str(e))
        return False

def get_accounts_from_env():
    """Dynamically fetches all LOGIN_USERNAME_X accounts from env vars."""
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
        print("⚠️ No accounts found in environment variables.")
        return

    print(f"🚀 Starting checks for {len(accounts)} accounts...")
    
    driver = None
    try:
        driver = get_driver()
        
        results = []
        for acc in accounts:
            success = process_account(driver, acc["user"], acc["pass"], acc["label"])
            results.append(success)
            
        if not all(results):
            print("⚠️ Some checks failed.")
            # exit(1) # Optional: Fail workflow if any check fails

    except Exception as e:
        print(f"🔥 Critical Driver Error: {e}")
    finally:
        if driver:
            driver.quit()
            print("🛑 Driver closed.")

if __name__ == "__main__":
    main()