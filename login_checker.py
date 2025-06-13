#!/usr/bin/env python3
import os
import logging
import requests
from datetime import datetime

# ——————————————
# Configuration
# ——————————————
LOGIN_URL     = 'https://www.himalayanuniversity.com/student/student_login.php'   # ← replace with your real URL
DASHBOARD_URL = 'https://example.com/after-login-dashboard'   # ← a page only available when logged in

USERNAME = os.getenv('AUTOLOGIN_USER')
PASSWORD = os.getenv('AUTOLOGIN_PASS')
if not USERNAME or not PASSWORD:
    raise SystemExit('❌ Missing AUTOLOGIN_USER or AUTOLOGIN_PASS in environment')

# ——————————————
# Logging setup
# ——————————————
logging.basicConfig(
    filename='login_checker.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def check_login():
    session = requests.Session()

    # 1) (Optional) grab hidden form fields or cookies
    # resp = session.get(LOGIN_URL)
    # parse resp.text for any hidden tokens if necessary...

    # 2) Build payload using the exact name= attributes:
    payload = {
        'frm_registration_no': USERNAME,  # your “Registration Number” field
        'frm_dob':             PASSWORD,  # your “Date of Birth” field
        # if there are any other hidden inputs, add them here
    }

    # 3) Submit the login form
    resp = session.post(LOGIN_URL, data=payload)
    
    # 4) Verify by requesting a protected page
    if resp.ok and session.get(DASHBOARD_URL).status_code == 200:
        logging.info('✅ Login succeeded')
    else:
        logging.error('❌ Login failed')

if __name__ == '__main__':
    logging.info('▶️ Running auto-loginer check')
    check_login()
