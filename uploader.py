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
    page.locator(config.SEL_USERNAME).fill(config.USERNAME)
    page.locator(config.SEL_PASSWORD).fill(config.PASSWORD)
    page.get_by_role("button", name=config.SEL_LOGIN_BUTTON).click()

    try:
        page.wait_for_url(config.HOME_URL, timeout=config.TIMEOUT)
    except PlaywrightTimeoutError:
        error_el = page.locator(".error")
        if error_el.count() > 0:
            raise RuntimeError(f"Login failed: {error_el.inner_text()}")
        raise RuntimeError(
            f"Login timed out — could not reach '{config.HOME_URL}' after submitting credentials."
        )

    print("Login successful.")


def upload_file_for_user(page: Page, user_id: str, file_path: Path) -> None:
    upload_url = config.EMPLOYEE_UPLOAD_URL.replace("{id}", user_id)
    result_url = config.EMPLOYEE_RESULT_URL.replace("{id}", user_id)

    print(f"  Navigating to {upload_url}")
    page.goto(upload_url)
    page.wait_for_selector(config.SEL_FILE_INPUT, timeout=config.TIMEOUT)

    page.locator(config.SEL_FILE_INPUT).set_input_files(str(file_path))
    page.get_by_role("button", name=config.SEL_UPLOAD_BUTTON).click()

    page.wait_for_url(f"**{result_url.split(config.BASE_URL)[-1]}", timeout=config.TIMEOUT)

    badge = page.locator(config.SEL_RESULT_BADGE)
    badge.wait_for(timeout=config.TIMEOUT)
    status = badge.get_attribute("class") or ""
    message = page.locator(config.SEL_RESULT_MESSAGE).inner_text()

    if config.SEL_SUCCESS_CLASS not in status:
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
                print(f"Skipping '{f.name}' — does not match {{user_id}}_{{name}} convention.")
    return results


def move_to_processed(file_path: Path) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_DIR / file_path.name
    counter = 1
    while dest.exists():
        dest = PROCESSED_DIR / f"{file_path.stem}_{counter}{file_path.suffix}"
        counter += 1
    file_path.rename(dest)


def run(batch_size: int) -> None:
    files_dir = Path(config.FILES_DIR)
    if not files_dir.exists():
        raise FileNotFoundError(f"Files directory not found: {files_dir}")

    files = collect_files(files_dir)
    if not files:
        print("No files found to upload.")
        return

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
        except Exception as e:
            error_msg = str(e).splitlines()[0] if isinstance(e, RuntimeError) else f"{type(e).__name__}: {str(e).splitlines()[0]}"
            print(f"\nERROR: {error_msg}")
            context.close()
            browser.close()
            print(json.dumps({"succeeded": [], "failed": [], "error": error_msg}, indent=2))
            return

        print()

        try:
            for i, (user_id, file_path) in enumerate(files, 1):
                print(f"[{i}/{len(files)}] {file_path.name} → user {user_id}")
                try:
                    upload_file_for_user(page, user_id, file_path)
                    print(f"  OK")
                    summary["succeeded"].append(user_id)
                except Exception as e:
                    print(f"  ERROR: {type(e).__name__}: {e}")
                    summary["failed"].append(user_id)
                finally:
                    move_to_processed(file_path)
                    print(f"  Moved to processed/")
                print()
        finally:
            context.close()
            browser.close()

    print(json.dumps(summary, indent=2))
