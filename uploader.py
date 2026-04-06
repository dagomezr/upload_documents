from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
import config


def login(page: Page) -> None:
    print(f"Navigating to login: {config.LOGIN_URL}")
    page.goto(config.LOGIN_URL)
    page.locator("#username").fill(config.USERNAME)
    page.locator("#password").fill(config.PASSWORD)
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/home", timeout=10_000)
    print("Login successful.")


def navigate_to_upload_page(page: Page) -> None:
    print(f"Navigating to upload page: {config.UPLOAD_URL}")
    page.goto(config.UPLOAD_URL)
    page.wait_for_selector("#file-input", timeout=10_000)
    print("Upload page loaded.")


def upload_document(page: Page, file_path: str) -> None:
    resolved = Path(file_path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    print(f"Uploading: {resolved.name}")
    page.locator("#file-input").set_input_files(str(resolved))
    page.get_by_role("button", name="Upload").click()

    # Wait for redirect to result page
    page.wait_for_url(f"**/users/{config.USER_ID}/result", timeout=10_000)

    # Read the outcome badge on the result page
    badge = page.locator(".badge")
    badge.wait_for(timeout=5_000)
    status = badge.get_attribute("class") or ""
    message = page.locator(".message").inner_text()

    if "success" in status:
        print(f"Upload succeeded: {message}")
    else:
        raise RuntimeError(f"Upload failed: {message}")


def run(file_path: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS, slow_mo=config.SLOW_MO)
        context = browser.new_context()
        page = context.new_page()

        try:
            login(page)
            navigate_to_upload_page(page)
            upload_document(page, file_path)
        except PlaywrightTimeoutError as e:
            print(f"Timeout: {e}")
            page.screenshot(path="error_screenshot.png")
            print("Screenshot saved to error_screenshot.png")
            raise
        finally:
            context.close()
            browser.close()
