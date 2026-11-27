import hashlib, json, random, sys, time, uuid
from pathlib import Path
import requests

API = "https://tapi.pureapk.com/v3"
AUTH = "qNKrYmW8SSUqJ73k3P2yfMxRTo3sJTR"
SECRET = "d33cb23fd17fda8ea38be504929b77ef"

WATCH = "--watch" in sys.argv
if WATCH:
    dev = {"abis": ["armeabi-v7a"], "android_id": "a1b2c3d4e5f60001",
           "brand": "samsung", "country": "United States", "country_code": "US",
           "language": "en-US", "manufacturer": "samsung", "mode": "SM-L500",
           "os_ver": "34", "os_ver_name": "14", "platform": 1, "product": "l500",
           "screen_height": 450, "screen_width": 450}
else:
    dev = {"abis": ["arm64-v8a", "armeabi-v7a"], "android_id": "a1b2c3d4e5f60001",
           "brand": "samsung", "country": "United States", "country_code": "US",
           "language": "en-US", "manufacturer": "samsung", "mode": "SM-G955F",
           "os_ver": "34", "os_ver_name": "14", "platform": 1, "product": "dream2lte",
           "screen_height": 2888, "screen_width": 1440}

u = str(uuid.uuid4())
project_a = json.dumps({
    "device_info": dev,
    "host_app_info": {"build_no": "873", "channel": "", "md5": "",
                      "pkg_name": "com.apkpure.aegon", "sdk_ver": "3.20.6309",
                      "version_code": 3206397, "version_name": "3.20.6309"},
    "net_info": {"carrier_code": 0, "ipv4": "", "ipv6": "", "mac_address": "",
                 "net_type": 1, "use_vpn": False, "wifi_bssid": "", "wifi_ssid": ""},
    "user_info": {"auth_key": AUTH, "country": "United States", "country_code": "US",
                  "guid": "", "language": "en-US", "qimei": "", "qimei_token": "",
                  "user_id": "", "uuid": u},
}, separators=(",", ":"))
ext = json.dumps({"ext_info": '{"gaid":"","oaid":""}',
                  "lbs_info": {"accuracy": 0.0, "city": "", "city_code": 0,
                               "country": "", "country_code": "", "district": "",
                               "latitude": 0.0, "longitude": 0.0, "province": "",
                               "street": ""}}, separators=(",", ":"))
base_headers = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; SM-G955F Build/AP2A.240805.005); APKPure/3.20.6309 (Aegon)",
    "Ual-Access-Businessid": "projecta", "Ual-Access-ProjectA": project_a,
    "Ual-Access-ExtInfo": ext, "Ual-Access-Sequence": str(uuid.uuid4()),
    "Ual-Access-Nonce": "0", "Ual-Access-Timestamp": "0", "Accept-Encoding": "gzip",
}

def signed(body):
    h = dict(base_headers)
    ts = str(int(time.time() * 1000))
    nonce = str(random.randint(10000000, 99999999))
    h["Ual-Access-Signature"] = hashlib.md5((body + ts + SECRET + nonce).encode()).hexdigest()
    h["Ual-Access-Nonce"] = nonce
    h["Ual-Access-Timestamp"] = ts
    h["Content-Type"] = "application/json; charset=utf-8"
    return h

s = requests.Session()
s.headers.update(base_headers)
print("WATCH PROFILE" if WATCH else "PHONE PROFILE", flush=True)
try:
    r = s.get(API + "/search_query_new",
              params={"hl": "en-US", "key": "strava", "page": "1",
                      "search_type": "active_search"}, timeout=60)
    print("search", r.status_code, len(r.text), r.text[:200], flush=True)
    data = r.json()
    for sec in data.get("data", {}).get("data", []):
        for item in sec.get("data", []):
            ai = item.get("app_info", {})
            if ai.get("package_name"):
                print("APP", ai["package_name"], ai.get("title"), ai.get("version_name"), flush=True)
except Exception as e:
    print("search ERR", str(e)[:250], flush=True)

try:
    body = json.dumps({"package_name": "com.strava", "hl": "en-US"})
    r = s.post(API + "/get_app_detail", data=body, headers=signed(body), timeout=60)
    print("detail", r.status_code, len(r.text), flush=True)
    raw = r.json()
    print("TOP KEYS", list(raw.keys()), flush=True)
    print("RAW", json.dumps(raw, ensure_ascii=False)[:4000], flush=True)
    d = raw.get("app_detail", {})
    print("AD KEYS", list(d.keys()), flush=True)
    print("version", d.get("version_name"), "code", d.get("version_code"), flush=True)
    print("asset", json.dumps(d.get("asset", {}))[:800], flush=True)
    Path("apkpure_detail.json").write_text(json.dumps(d, ensure_ascii=False, indent=2))
except Exception as e:
    print("detail ERR", str(e)[:250], flush=True)
