import os
from dotenv import load_dotenv

load_dotenv()

# --- Credentials ---
USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")

# --- URLs ---
# Use {id} as placeholder in employee URLs, e.g. http://localhost:8080/users/{id}/upload
BASE_URL    = os.getenv("BASE_URL", "http://localhost:8080")
LOGIN_URL   = os.getenv("LOGIN_URL", f"{BASE_URL}/login")
HOME_URL    = os.getenv("HOME_URL", "**/home")
EMPLOYEE_UPLOAD_URL = os.getenv("EMPLOYEE_UPLOAD_URL", f"{BASE_URL}/users/{{id}}/upload")
EMPLOYEE_RESULT_URL = os.getenv("EMPLOYEE_RESULT_URL", f"{BASE_URL}/users/{{id}}/result")

# --- Selectors ---
SEL_USERNAME       = os.getenv("SEL_USERNAME", "#username")
SEL_PASSWORD       = os.getenv("SEL_PASSWORD", "#password")
SEL_LOGIN_BUTTON   = os.getenv("SEL_LOGIN_BUTTON", "Login")
SEL_FILE_INPUT     = os.getenv("SEL_FILE_INPUT", "#file-input")
SEL_UPLOAD_BUTTON  = os.getenv("SEL_UPLOAD_BUTTON", "Upload")
SEL_RESULT_BADGE   = os.getenv("SEL_RESULT_BADGE", ".badge")
SEL_RESULT_MESSAGE = os.getenv("SEL_RESULT_MESSAGE", ".message")
SEL_SUCCESS_CLASS  = os.getenv("SEL_SUCCESS_CLASS", "success")

# --- Files ---
FILES_DIR = os.getenv("FILES_DIR", "files")

# --- Playwright ---
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO  = int(os.getenv("SLOW_MO", "0"))
TIMEOUT  = int(os.getenv("TIMEOUT", "10000"))  # milliseconds
