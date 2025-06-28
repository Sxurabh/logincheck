from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.text import MIMEText
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

# Email configuration
SENDER_EMAIL    = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL  = os.getenv("RECEIVER_EMAIL")
SMTP_SERVER     = "smtp.gmail.com"
SMTP_PORT       = 587

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"Email notification sent: {subject}")
    except Exception as e:
        print(f"Failed to send email '{subject}': {e}")

# --- Selenium setup ---
options = Options()
options.binary_location = "/usr/bin/chromium-browser"    # Ubuntu’s Chromium binary
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

    wait.until(EC.visibility_of_element_located((By.ID, USERNAME_FIELD_ID))).send_keys(USERNAME)
    print("Entered username")

    wait.until(EC.visibility_of_element_located((By.ID, PASSWORD_FIELD_ID))).send_keys(PASSWORD)
    print("Entered password")

    wait.until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID))).click()
    print("Clicked login button")

    try:
        wait.until(EC.url_to_be(EXPECTED_URL))
        success_msg = f"Login successful at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        print(success_msg)
        send_email("✅ Login Success", success_msg)
    except TimeoutException:
        error_message = "Login failed: did not redirect to the expected URL in time."
        print(error_message)
        send_email("⚠️ Login Failure", error_message)

except TimeoutException:
    error_message = "Timeout: Element not found or page too slow."
    print(error_message)
    send_email("⚠️ Login Failure", error_message)
except Exception as e:
    error_message = f"Unexpected error: {e}"
    print(error_message)
    send_email("⚠️ Login Failure", error_message)
finally:
    driver.quit()
    print("Browser closed")
