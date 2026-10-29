import os
import urllib.request
import json

token = os.environ.get("GITHUB_TOKEN", "")
req = urllib.request.Request("https://api.github.com/repos/gnshx/repomedic-demo-repo", headers={
    "Authorization": f"token {token}",
    "User-Agent": "test",
})

try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print("Status:", r.status)
        d = json.loads(r.read())
        print("Repo exists! URL:", d.get("html_url"))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
