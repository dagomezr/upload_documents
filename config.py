import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
LOGIN_URL = f"{BASE_URL}/login"

USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")

FILES_DIR = os.getenv("FILES_DIR", "files")

HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
