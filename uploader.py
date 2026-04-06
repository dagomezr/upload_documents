import json
import configparser
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
import config

PROCESSED_DIR = Path(config.FILES_DIR) / "processed"
PROPERTIES_FILE = Path("test_server/test.properties")


def load_properties() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(inline_comment_prefixes=("#",))
    cfg.read_string("[default]\n" + PROPERTIES_FILE.read_text())
    return cfg


def login(page: Page) -> None:
    print(f"Logging in as {config.USERNAME}...")
    page.goto(config.LOGIN_URL)
    page.locator("#username").fill(config.USERNAME)
    page.locator("#password").fill(config.PASSWORD)
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/home", timeout=10_000)
    print("Login successful.")


def upload_file_for_user(page: Page, user_id: str, file_path: Path) -> None:
    upload_url = f"{config.BASE_URL}/users/{user_id}/upload"

    print(f"  Navigating to {upload_url}")
    page.goto(upload_url)
    page.wait_for_selector("#file-input", timeout=10_000)

    page.locator("#file-input").set_input_files(str(file_path))
    page.get_by_role("button", name="Upload").click()

    page.wait_for_url(f"**/users/{user_id}/result", timeout=10_000)

    badge = page.locator(".badge")
    badge.wait_for(timeout=5_000)
    status = badge.get_attribute("class") or ""
    message = page.locator(".message").inner_text()

    if "success" not in status:
        raise RuntimeError(message)


def collect_files(folder: Path) -> list[tuple[str, Path]]:
    """
    Scan folder for files matching {user_id}_contract.pdf
    Returns a list of (user_id, file_path) sorted numerically by user_id.
    """
    results = []
    for f in sorted(folder.iterdir(), key=lambda f: int(f.stem.split("_")[0]) if f.stem.split("_")[0].isdigit() else float("inf")):
        if f.is_file() and not f.name.startswith("."):
            parts = f.stem.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit():
                results.append((parts[0], f))
            else:
                print(f"Skipping '{f.name}' — does not match {{user_id}}_contract.pdf convention.")
    return results


def move_to_processed(file_path: Path) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_DIR / file_path.name
    # Avoid overwrite — append a counter if name already exists
    counter = 1
    while dest.exists():
        dest = PROCESSED_DIR / f"{file_path.stem}_{counter}{file_path.suffix}"
        counter += 1
    file_path.rename(dest)


def run() -> None:
    files_dir = Path(config.FILES_DIR)
    if not files_dir.exists():
        raise FileNotFoundError(f"Files directory not found: {files_dir}")

    files = collect_files(files_dir)
    if not files:
        print("No files found to upload.")
        return

    cfg = load_properties()
    batch_size = cfg.getint("default", "batch_size", fallback=0)
    if batch_size > 0:
        files = files[:batch_size]
        print(f"Batch size limit: {batch_size}")

    print(f"Processing {len(files)} file(s).\n")

    summary: dict[str, list[str]] = {"succeeded": [], "failed": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS, slow_mo=config.SLOW_MO)
        context = browser.new_context()
        page = context.new_page()

        try:
            login(page)
            print()

            for i, (user_id, file_path) in enumerate(files, 1):
                print(f"[{i}/{len(files)}] {file_path.name} → user {user_id}")
                try:
                    upload_file_for_user(page, user_id, file_path)
                    print(f"  OK")
                    summary["succeeded"].append(user_id)
                except (PlaywrightTimeoutError, RuntimeError) as e:
                    print(f"  ERROR: {e}")
                    page.screenshot(path=f"error_{file_path.stem}.png")
                    print(f"  Screenshot saved to error_{file_path.stem}.png")
                    summary["failed"].append(user_id)
                finally:
                    move_to_processed(file_path)
                    print(f"  Moved to processed/")
                print()

        finally:
            context.close()
            browser.close()

    print(json.dumps(summary, indent=2))
