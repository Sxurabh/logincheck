from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import smtplib
from email.mime.text import MIMEText
import time
import os

# Configuration variables
LOGIN_URL = "https://www.himalayanuniversity.com/student/student_login.php"
USERNAME = os.getenv("LOGIN_USERNAME")  # Use GitHub Secrets
PASSWORD = os.getenv("LOGIN_PASSWORD")  # Use GitHub Secrets
USERNAME_FIELD_ID = "frm_registration_no"
PASSWORD_FIELD_ID = "frm_dob"
LOGIN_BUTTON_ID = "div_load"
EXPECTED_URL = "https://www.himalayanuniversity.com/student/index.php"

# Email configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(subject, body):
    """Send an email notification."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"Email notification sent successfully: {subject}")
    except Exception as e:
        print(f"Failed to send email '{subject}': {e}")

# Set up Chrome options for headless mode
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Initialize the Chrome driver
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

try:
    # Navigate to the login page
    driver.get(LOGIN_URL)
    print(f"Opened {LOGIN_URL}")

    # Find and fill the username field
    username_field = wait.until(EC.visibility_of_element_located((By.ID, USERNAME_FIELD_ID)))
    username_field.send_keys(USERNAME)
    print("Entered username")

    # Find and fill the password field
    password_field = wait.until(EC.visibility_of_element_located((By.ID, PASSWORD_FIELD_ID)))
    password_field.send_keys(PASSWORD)
    print("Entered password")

    # Find and click the login button
    login_button = wait.until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID)))
    login_button.click()
    print("Clicked login button")

    # Verify successful login by checking the URL
    try:
        wait.until(EC.url_to_be(EXPECTED_URL))
        success_msg = f"Login successful at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        print(success_msg)
        send_email("✅ Login Success", success_msg)
    except TimeoutException:
        error_message = "Login failed: did not redirect to the expected URL within the time limit."
        print(error_message)
        send_email("⚠️ Login Failure Alert", error_message)

except TimeoutException:
    error_message = "Timeout: Element not found or page took too long to load."
    print(error_message)
    send_email("⚠️ Login Failure Alert", error_message)
except Exception as e:
    error_message = f"Unexpected error: {e}"
    print(error_message)
    send_email("⚠️ Login Failure Alert", error_message)
finally:
    driver.quit()
    print("Browser closed")
