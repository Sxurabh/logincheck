from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import time

# Configuration variables (replace with your actual values)
LOGIN_URL = "https://www.himalayanuniversity.com/student/student_login.php"
USERNAME = "5045101012180086"
PASSWORD = "16071998"
USERNAME_FIELD_ID = "frm_registration_no"
PASSWORD_FIELD_ID = "frm_dob"
LOGIN_BUTTON_ID = "div_load"
EXPECTED_URL = "https://www.himalayanuniversity.com/student/index.php"

# Set up Chrome options for headless mode
options = Options()
options.add_argument("--headless")

# Initialize the Chrome driver with headless options
driver = webdriver.Chrome(options=options)  # Ensure ChromeDriver is in your PATH
wait = WebDriverWait(driver, 10)  # Explicit wait with a 10-second timeout

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
        print("Login successful!")
    except TimeoutException:
        print("Login failed: did not redirect to the expected URL within the time limit.")

except TimeoutException:
    print("Timeout: Element not found or page took too long to load.")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    # Clean up by closing the browser
    time.sleep(5)  # Optional delay before closing
    driver.quit()
    print("Browser closed")