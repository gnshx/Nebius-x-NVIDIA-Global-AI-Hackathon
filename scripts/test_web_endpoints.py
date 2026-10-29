#!/usr/bin/env python3
"""
Test all Next.js web application endpoints and verify responses.
"""
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:3000"

ENDPOINTS = [
    "/",
    "/runs",
    "/repositories",
    "/settings",
    "/runs/55f677a5-01af-4011-857a-bbc83740a908",
    "/runs/d723aba3-d914-45c0-ae60-85b35e9cb958",
    "/assets/repomedic_pitch.mp3",
    "/assets/repomedic_demo.mp4",
    "/assets/architecture.jpg",
    "/assets/dashboard.jpg",
    "/assets/logo.jpg",
]

def main():
    print("🧪 Testing RepoMedic Web Application Endpoints...")
    all_ok = True
    for ep in ENDPOINTS:
        url = f"{BASE_URL}{ep}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RepoMedic-Tester/1.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                code = res.status
                content_len = len(res.read())
                print(f"  ✅ {ep:<48} HTTP {code} ({content_len:,} bytes)")
        except urllib.error.HTTPError as e:
            print(f"  ❌ {ep:<48} HTTP {e.code}")
            all_ok = False
        except Exception as exc:
            print(f"  ❌ {ep:<48} FAILED: {exc}")
            all_ok = False
            
    if all_ok:
        print("\n🎉 All web routes and static assets returned HTTP 200 OK!")
        sys.exit(0)
    else:
        print("\n⚠️ Some routes failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
