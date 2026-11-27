import base64, json, os, sys, urllib.request, urllib.error
from pathlib import Path
TOKEN = sys.argv[1]
REPO = "Louzy2020/apk-shell-runner"
API = "https://api.github.com/repos/" + REPO + "/contents/"
HDR = {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
       "User-Agent": "apk-uploader", "Content-Type": "application/json"}

def put(name):
    p = Path(name)
    if not p.exists():
        print("skip missing", name); return
    url = API + name
    sha = None
    try:
        req = urllib.request.Request(url, headers=HDR)
        sha = json.load(urllib.request.urlopen(req, timeout=30)).get("sha")
    except Exception:
        pass
    payload = {"message": "upload " + name,
               "content": base64.b64encode(p.read_bytes()).decode()}
    if sha:
        payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers=HDR, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            print("uploaded", name, r.status, p.stat().st_size)
    except urllib.error.HTTPError as e:
        print("upload failed", name, e.code, e.read().decode()[:200])

for n in ("result.txt", "strava_wearos_1.45.apkm"):
    put(n)
