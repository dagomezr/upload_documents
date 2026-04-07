import json
import re
import subprocess
import shutil
import time
from pathlib import Path

FILES_DIR = Path("files")
PROCESSED_DIR = FILES_DIR / "processed"
TEST_PROPERTIES = Path("test_server/test.properties")
ENV_FILE = Path(".env")

SCENARIOS = [
    "Happy path",
    "Invalid credentials",
    "Login timeout",
    "Error loading user 2 and 4",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_properties(login_delay: int = 0, upload_error_ids: str = "") -> None:
    TEST_PROPERTIES.write_text(
        f"login_delay_seconds={login_delay}\n"
        f"upload_error_ids={upload_error_ids}\n"
    )


def set_env_credentials(username: str, password: str, timeout: int = 10000) -> None:
    lines = ENV_FILE.read_text().splitlines()
    updated = []
    for line in lines:
        if line.startswith("USERNAME="):
            updated.append(f"USERNAME={username}")
        elif line.startswith("PASSWORD="):
            updated.append(f"PASSWORD={password}")
        elif line.startswith("TIMEOUT="):
            updated.append(f"TIMEOUT={timeout}")
        else:
            updated.append(line)
    ENV_FILE.write_text("\n".join(updated) + "\n")


def restore_files() -> None:
    for f in PROCESSED_DIR.glob("*.pdf"):
        dest = FILES_DIR / f.name
        if not dest.exists():
            shutil.move(str(f), dest)


def run_scenario(batch_size: int = 5) -> str:
    result = subprocess.run(
        ["python", "main.py", "--batch-size", str(batch_size)],
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


def extract_json(output: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", output)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"error": "No JSON output found"}


def print_scenario(index: int, name: str, output: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  Scenario {index}: {name}")
    print(f"{'=' * 60}")
    print(output.strip())


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def scenario_happy_path() -> dict:
    restore_files()
    write_properties(login_delay=0, upload_error_ids="")
    set_env_credentials("admin", "password123")
    output = run_scenario(batch_size=5)
    print_scenario(1, SCENARIOS[0], output)
    return extract_json(output)


def scenario_invalid_credentials() -> dict:
    restore_files()
    write_properties(login_delay=0, upload_error_ids="")
    set_env_credentials("admin", "wrongpassword")
    output = run_scenario(batch_size=5)
    print_scenario(2, SCENARIOS[1], output)
    return extract_json(output)


def scenario_login_timeout() -> dict:
    restore_files()
    write_properties(login_delay=40, upload_error_ids="")
    set_env_credentials("admin", "password123")
    print("\n[!] Login timeout scenario — will take ~30s for Playwright to time out...")
    output = run_scenario(batch_size=5)
    print_scenario(3, SCENARIOS[2], output)
    return extract_json(output)


def scenario_upload_errors() -> dict:
    restore_files()
    write_properties(login_delay=0, upload_error_ids="2,4")
    set_env_credentials("admin", "password123")
    output = run_scenario(batch_size=5)
    print_scenario(4, SCENARIOS[3], output)
    return extract_json(output)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting test scenarios — make sure the test server is running on port 8080.")
    time.sleep(1)

    results = {
        SCENARIOS[0]: scenario_happy_path(),
        SCENARIOS[1]: scenario_invalid_credentials(),
        SCENARIOS[2]: scenario_login_timeout(),
        SCENARIOS[3]: scenario_upload_errors(),
    }

    # Reset to clean state
    write_properties(login_delay=0, upload_error_ids="")
    set_env_credentials("admin", "password123")
    restore_files()

    print(f"\n{'=' * 60}")
    print("  All scenarios completed. Config reset to defaults.")
    print(f"{'=' * 60}")
    print("\n--- JSON Summary ---\n")
    print(json.dumps(results, indent=2))
