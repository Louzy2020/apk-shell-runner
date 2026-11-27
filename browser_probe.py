import traceback
from pathlib import Path

URL = ("https://www.apkmirror.com/apk/strava-inc/"
       "strava-training-track-running-cycling-swimming-wear-os/"
       "strava-training-track-running-cycling-swimming-wear-os-1-45-release/"
       "strava-run-bike-hike-wear-os-1-45-android-apk-download/")

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True,
                                        args=["--no-sandbox", "--disable-dev-shm-usage"])
            print("using installed chrome", flush=True)
        except Exception as e:
            print("chrome channel failed:", str(e)[:200], flush=True)
            browser = p.chromium.launch(headless=True,
                                        args=["--no-sandbox", "--disable-dev-shm-usage"])
            print("using bundled chromium", flush=True)
        page = browser.new_page()
        page.goto(URL, timeout=120000, wait_until="domcontentloaded")
        print("initial:", page.title(), page.url, flush=True)
        page.wait_for_timeout(12000)
        html = page.content()
        print("after wait:", page.title(), len(html), flush=True)
        print(html[:300].replace("\n", " "), flush=True)
        Path("browser_page.html").write_text(html, encoding="utf-8")
        cookies = page.context.cookies()
        Path("browser_cookies.json").write_text(__import__("json").dumps(cookies))
        print("cookies:", len(cookies), flush=True)
        browser.close()
except Exception:
    traceback.print_exc()
