import hashlib, re, sys, traceback
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = "https://www.apkmirror.com"
SLUG = ("apk/strava-inc/"
        "strava-training-track-running-cycling-swimming-wear-os/")
PAGE = (BASE + "/" + SLUG +
        "strava-training-track-running-cycling-swimming-wear-os-1-45-release/"
        "strava-run-bike-hike-wear-os-1-45-android-apk-download/")
FNAME = "com.strava_1.45-78701_1arch_1dpi_9lang_cc1ca26ad7e8ad411c98b543de1d86d7_apkmirror.com.apkm"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
EXPECTED = "e12bf4bc34d2575544bed63d4d0b959578d28786b08fc51efb52ed9c25ee4e49"
OUT = Path("strava_wearos_1.45.apkm")
LOG = []

def log(msg):
    LOG.append(str(msg)); print(msg, flush=True)

def absu(href, base=BASE):
    if href.startswith("http"):
        return href
    return base.rstrip("/") + "/" + href.lstrip("/")

def save_stream(sess, url):
    log("GET " + url)
    with sess.get(url, headers=H, stream=True, timeout=240) as resp:
        log("  status " + str(resp.status_code) + " type " + str(resp.headers.get("content-type")))
        resp.raise_for_status()
        tmp = OUT.with_suffix(".part")
        with tmp.open("wb") as f:
            for chunk in resp.iter_content(1 << 20):
                if chunk:
                    f.write(chunk)
        size = tmp.stat().st_size
        log("  size " + str(size))
        if size < 1_000_000:
            raise RuntimeError("文件过小, 不是 APK")
        head = tmp.open("rb").read(4)
        if head[:2] != b"PK":
            raise RuntimeError("文件内容不是 zip/apk: " + repr(head))
        tmp.replace(OUT)
        return size

def candidates_from_html(html, base):
    out = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html):
        u = m.group(1)
        if any(k in u.lower() for k in ("download.apkmirror.com", ".apkm", ".apk?" , "download.php", "/download/")):
            out.append(absu(u, base))
    # 处理 data-* 属性里的链接
    for m in re.finditer(r'data-[a-z-]*=["\']([^"\']*(?:download|\.apkm)[^"\']*)["\']', html, re.I):
        u = m.group(1)
        if u.startswith("http") or u.startswith("/"):
            out.append(absu(u, base))
    seen = set(); res = []
    for u in out:
        if u not in seen:
            seen.add(u); res.append(u)
    return res

s = requests.Session()
ok = False
# 路径 1: 已知直链(搜索缓存里的确切文件名)
direct = (BASE + "/download.apkmirror.com/" + SLUG +
          "strava-training-track-running-cycling-swimming-wear-os-1-45-release/"
          "strava-run-bike-hike-wear-os-1-45-android-apk-download/" + FNAME)
direct = direct.replace(BASE + "/download.apkmirror.com/", "https://download.apkmirror.com/")
try:
    save_stream(s, direct)
    ok = True
except Exception as e:
    log("路径1失败: " + str(e)[:200])

# 路径 2: 版本页 -> 下载按钮 -> 确认页 -> 直链
if not ok:
    try:
        r = s.get(PAGE, headers=H, timeout=90)
        log("版本页 status " + str(r.status_code) + " len " + str(len(r.text)))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        urls = []
        for sel in ("a.downloadButton[href]", "a[href*='/download/']", "a[href*='download.php']"):
            for a in soup.select(sel):
                u = a.get("href")
                if u:
                    urls.append(absu(u, PAGE))
        urls += candidates_from_html(r.text, PAGE)
        seen = set(); urls = [u for u in urls if not (u in seen or seen.add(u))]
        log("候选下载页 " + str(len(urls)) + " 个")
        for u in urls[:8]:
            try:
                r2 = s.get(u, headers=H, timeout=90)
                log("  确认页 " + str(r2.status_code) + " " + u[:140])
                if r2.status_code != 200:
                    continue
                c = BeautifulSoup(r2.text, "html.parser")
                finals = []
                for a in c.select("a[href]"):
                    href = a.get("href", "")
                    if any(k in href.lower() for k in ("download.apkmirror.com", ".apkm", "download.php")):
                        finals.append(absu(href, u))
                finals += candidates_from_html(r2.text, u)
                # 过滤掉 HTML 页面, 优先真实文件
                finals = [x for x in finals if ".apkm" in x or "download.apkmirror.com" in x]
                seen2 = set(); finals = [x for x in finals if not (x in seen2 or seen2.add(x))]
                for f in finals[:6]:
                    try:
                        save_stream(s, f)
                        ok = True
                        break
                    except Exception as e:
                        log("    直链失败: " + str(e)[:150])
                if ok:
                    break
            except Exception as e:
                log("  确认页失败: " + str(e)[:150])
    except Exception:
        log(traceback.format_exc()[:1500])

if not ok:
    Path("result.txt").write_text("FAIL\n" + "\n".join(LOG)[:6000])
    sys.exit(1)

h = hashlib.sha256()
with OUT.open("rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
actual = h.hexdigest()
status = "OK" if actual == EXPECTED else "HASH_MISMATCH"
Path("result.txt").write_text(status + " sha256=" + actual +
                              " size=" + str(OUT.stat().st_size) + "\n" + "\n".join(LOG)[:5000])
log("sha256 " + actual + " expected " + EXPECTED)
