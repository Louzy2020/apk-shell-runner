import sys, traceback
from pathlib import Path

URL = ("https://www.apkmirror.com/apk/strava-inc/"
       "strava-training-track-running-cycling-swimming-wear-os/"
       "strava-training-track-running-cycling-swimming-wear-os-1-45-release/"
       "strava-run-bike-hike-wear-os-1-45-android-apk-download/")

try:
    from curl_cffi import requests as cr
    for imp in ("chrome", "chrome124", "safari17_0"):
        try:
            s = cr.Session(impersonate=imp)
            r = s.get(URL, timeout=60)
            print(imp, r.status_code, len(r.text), r.url, flush=True)
            print(r.text[:200].replace("\n", " "), flush=True)
            if r.status_code == 200 and "Just a moment" not in r.text:
                Path("apkm_page.html").write_text(r.text, encoding="utf-8")
                print("SAVED PAGE", len(r.text), flush=True)
                break
        except Exception as e:
            print(imp, "ERR", str(e)[:200], flush=True)
except Exception:
    traceback.print_exc()
