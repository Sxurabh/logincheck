#!/usr/bin/env python3
import os
import logging
import requests

# ——————————————
# Configuration
# ——————————————
# Direct login URL for Himalayan University student portal
LOGIN_URL = 'https://www.himalayanuniversity.com/student/student_login.php'

# Load credentials from environment
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

    # Build payload using the form field names
    payload = {
        'frm_registration_no': USERNAME,  # "Registration Number" field
        'frm_dob': PASSWORD,              # "Date of Birth" field
    }

    # Submit the login form without following redirects
    resp = session.post(LOGIN_URL, data=payload, allow_redirects=False)

    # Check for redirect (HTTP 301/302) to determine success
    if resp.status_code in (301, 302):
        logging.info('✅ Login succeeded (redirect detected)')
    else:
        logging.error(f'❌ Login failed (status code {resp.status_code})')

if __name__ == '__main__':
    logging.info('▶️ Running auto-loginer check')
    check_login()
