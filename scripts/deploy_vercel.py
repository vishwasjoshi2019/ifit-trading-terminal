import hashlib
import os
import requests

TOKEN = os.environ.get("VERCEL_TOKEN") or os.environ.get("VERCEL_AUTH_TOKEN", "")
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

def get_sha1(filepath):
    h = hashlib.sha1()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def upload_file(filepath):
    sha = get_sha1(filepath)
    size = os.path.getsize(filepath)
    url = f"https://api.vercel.com/v2/files"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/octet-stream",
        "x-vercel-digest": sha,
        "Content-Length": str(size),
    }
    with open(filepath, "rb") as f:
        r = requests.post(url, headers=headers, data=f)
    print(f"Uploaded {filepath} -> {r.status_code}")
    return sha, size

def deploy():
    files_payload = []
    for root, _, files in os.walk(DIST_DIR):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, DIST_DIR)
            sha, size = upload_file(full_path)
            files_payload.append({
                "file": rel_path,
                "sha": sha,
                "size": size,
            })

    deploy_url = "https://api.vercel.com/v13/deployments"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "name": "ifit-trading-terminal",
        "files": files_payload,
        "projectSettings": {
            "framework": None,
        },
        "target": "production",
        "routes": [
            {"handle": "filesystem"},
            {"src": "/(.*)", "dest": "/index.html"}
        ]
    }
    r = requests.post(deploy_url, headers=headers, json=body)
    print("Deployment response:", r.status_code)
    try:
        data = r.json()
        print("URL:", data.get("url"))
        print("Alias:", data.get("alias"))
        print("ReadyState:", data.get("readyState"))
        print("Full response:", data)
    except Exception as e:
        print("Error parsing json:", r.text)

if __name__ == "__main__":
    deploy()
