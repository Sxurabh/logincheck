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

# Suppress SSL warnings for the result check if verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── Configuration ─────────────────────────────────────────────────────────────
LOGIN_URL       = "https://www.himalayanuniversity.com/student/student_login.php"
DASHBOARD_URL   = "https://www.himalayanuniversity.com/student/index.php"
RESULT_PAGE_URL = "https://www.himalayanuniversity.com/student/student_campus_result.php"

# HTML Element IDs (Login Page)
USERNAME_FIELD_ID = "frm_registration_no"
PASSWORD_FIELD_ID = "frm_dob"
LOGIN_BUTTON_ID   = "div_load"

# Telegram Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

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

def check_result_download(driver):
    """
    Navigates to the result page and checks if the download link is healthy.
    Returns: (is_success: bool, status_message: str)
    """
    print("   ↳ Checking Result Download capability...")
    try:
        # Navigate directly to Result Page
        driver.get(RESULT_PAGE_URL)
        
        wait = WebDriverWait(driver, 10)
        
        # Look for the 'Download' button based on your screenshot
        # It's a <button> inside an <a> tag
        download_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(text(), 'Download')]")
        ))
        
        # Get parent <a> tag to extract the actual href
        parent_anchor = download_btn.find_element(By.XPATH, "./..")
        download_href = parent_anchor.get_attribute("href")
        
        if not download_href:
            return False, "Download link not found in HTML"

        print(f"   ↳ Found download URL: {download_href[:50]}...")

        # Perform a HEAD/GET request to check if the link actually works (returns 200 vs 500)
        # We use a custom User-Agent to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # verify=False prevents SSL errors on some legacy edu sites
        # timeout=15 ensures we don't hang if the server is dead
        r = requests.get(download_href, headers=headers, timeout=15, verify=False)
        
        if r.status_code == 200:
            return True, "Available ✅"
        elif r.status_code == 500:
            # Specific message for the error you are facing
            return False, "⛔ <b>HTTP 500 Error</b> (This page isn’t working)"
        else:
            return False, f"⚠️ Failed (Status: {r.status_code})"

    except TimeoutException:
        return False, "⚠️ Download button not found on Result page"
    except Exception as e:
        return False, f"⚠️ Error checking result: {str(e)}"

def check_single_login(username, password, label):
    """Performs login and result check for a given user."""
    print(f"\n--- Starting Check for: {label} ---")
    
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222") # CI stability
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")

    service = Service(ChromeDriverManager().install())
    
    # Initialize driver
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"❌ Failed to initialize Driver for {label}: {e}")
        return False

    wait = WebDriverWait(driver, 15)
    login_status = "Failed"
    result_status = "Skipped"
    result_msg = "Skipped"
    student_name = "Unknown"

    try:
        # 1. Login Process
        driver.get(LOGIN_URL)
        wait.until(EC.visibility_of_element_located((By.ID, USERNAME_FIELD_ID))).send_keys(username)
        wait.until(EC.visibility_of_element_located((By.ID, PASSWORD_FIELD_ID))).send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID))).click()

        try:
            # Wait for redirect to Dashboard
            wait.until(EC.url_to_be(DASHBOARD_URL))
            login_status = "Success"
            
            # 2. Extract Name
            try:
                name_element = driver.find_element(By.CLASS_NAME, "log_txt")
                raw_text = name_element.text.strip()
                if "welcome" in raw_text.lower():
                    student_name = raw_text.lower().split("welcome")[-1].strip().title()
                else:
                    student_name = raw_text
            except Exception:
                print("   ↳ Could not extract name")

            # 3. Check Result Download
            is_download_ok, result_msg = check_result_download(driver)
            result_status = "Success" if is_download_ok else "Failed"

            # 4. Prepare Telegram Message
            # Choose emoji based on result status
            res_emoji = "✅" if is_download_ok else "❌"
            
            msg = (
                f"👤 <b>User: {student_name}</b>\n"
                f"✅ <b>Login:</b> Success\n"
                f"{res_emoji} <b>Result:</b> {result_msg}\n"
                f"🏷️ {label}\n"
                f"🕒 {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            subject_line = f"{label}: Status Update"
            if not is_download_ok:
                subject_line = f"{label}: Action Required ⚠️"
                
            send_telegram(subject_line, msg)
            print(f"Check Complete: Login=Success, Result={result_msg}")

        except TimeoutException:
            msg = f"Login failed for {label}: Redirection timed out."
            print(msg)
            send_telegram(f"{label}: Login Failed ❌", msg)

    except Exception as e:
        msg = f"Critical Error checking {label}: {str(e)}"
        print(msg)
        send_telegram(f"{label}: Script Error ❌", msg)
    finally:
        driver.quit()
    
    return login_status == "Success"

def main():
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

if __name__ == "__main__":
    main()