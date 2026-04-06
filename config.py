import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
LOGIN_URL = f"{BASE_URL}/login"
USER_ID = os.getenv("USER_ID", "1")
UPLOAD_URL = f"{BASE_URL}/users/{USER_ID}/upload"
RESULT_URL = f"{BASE_URL}/users/{USER_ID}/result"

USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")

HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
