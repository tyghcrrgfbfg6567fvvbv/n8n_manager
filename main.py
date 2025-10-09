import os
import subprocess
import json
import shutil
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv, set_key
import requests
from pathlib import Path
from urllib.parse import urljoin
from time import sleep

ROOT = Path(__file__).parent.resolve()
PROJECTS_DIR = ROOT / "project"
PROJECTS_DIR.mkdir(exist_ok=True)

load_dotenv(ROOT / ".env")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
DEFAULT_PORT = int(os.getenv("PORT", "5000"))
N8N_PORT = os.getenv("N8N_PORT", "5678")

app = Flask(__name__, static_folder="static", template_folder="templates")

GITHUB_API = "https://api.github.com/"

def get_headers():
    token = os.getenv("GITHUB_TOKEN", "")
    return {"Authorization": f"token {token}"} if token else {}

def refresh_env_values():
    # reload environment values in runtime (useful if updated from UI)
    load_dotenv(ROOT / ".env", override=True)

@app.route("/")
def index():
    refresh_env_values()
    return render_template("index.html")

@app.route("/api/env", methods=["GET"])
def api_env():
    refresh_env_values()
    return jsonify({
        "GITHUB_USERNAME": os.getenv("GITHUB_USERNAME", ""),
        "GITHUB_TOKEN": "SET" if os.getenv("GITHUB_TOKEN") else "",
        "REPO": os.getenv("REPO", ""),
        "PORT": os.getenv("PORT", str(DEFAULT_PORT)),
        "N8N_PORT": os.getenv("N8N_PORT", N8N_PORT)
    })

@app.route("/api/env", methods=["POST"])
def api_env_update():
    data = request.json or {}
    # update .env file keys sparingly
    for key in ("GITHUB_TOKEN","GITHUB_USERNAME","REPO","PORT","N8N_PORT"):
        if key in data:
            set_key(str(ROOT / ".env"), key, str(data[key]))
    refresh_env_values()
    return jsonify({"ok": True})

@app.route("/api/repos", methods=["GET"])
def list_repos():
    refresh_env_values()
    token = os.getenv("GITHUB_TOKEN", "")
    username = os.getenv("GITHUB_USERNAME", "")
    if not token:
        return jsonify({"error": "GITHUB_TOKEN not set in .env"}), 400

    url = urljoin(GITHUB_API, "user/repos")
    params = {"per_page": 100, "sort": "updated"}
    resp = requests.get(url, headers=get_headers(), params=params)
    if resp.status_code != 200:
        return jsonify({"error": "GitHub API error", "detail": resp.text}), 500
    repos = resp.json()
    # Prepare list with essential fields
    simplified = []
    for r in repos:
        simplified.append({
            "name": r.get("name"),
            "full_name": r.get("full_name"),
            "html_url": r.get("html_url"),
            "private": r.get("private"),
            "ssh_url": r.get("ssh_url"),
            "clone_url": r.get("clone_url"),
            "updated_at": r.get("updated_at")
        })
    return jsonify({"repos": simplified})

@app.route("/api/create", methods=["POST"])
def create_repo():
    refresh_env_values()
    data = request.json or {}
    name = data.get("name", "").strip()
    private = bool(data.get("private", False))
    description = data.get("description", "Created via n8n_manager")

    token = os.getenv("GITHUB_TOKEN", "")
    username = os.getenv("GITHUB_USERNAME", "")
    if not token or not username:
        return jsonify({"error": "Set GITHUB_TOKEN and GITHUB_USERNAME in .env"}), 400
    if not name:
        return jsonify({"error": "Repository name required"}), 400

    # Check if repo exists
    repo_check = requests.get(urljoin(GITHUB_API, f"repos/{username}/{name}"), headers=get_headers())
    if repo_check.status_code == 200:
        # already exists on GitHub -> ensure local clone
        repo_info = repo_check.json()
        try:
            local_path = clone_or_pull_local_repo(repo_info.get("clone_url"), name)
            return jsonify({"ok": True, "msg": "Repo already existed; synced locally", "local_path": str(local_path)})
        except Exception as e:
            return jsonify({"error": "Failed to sync existing repo", "detail": str(e)}), 500

    # Create repo on GitHub
    payload = {"name": name, "private": private, "description": description, "auto_init": False}
    create_resp = requests.post(urljoin(GITHUB_API, "user/repos"), headers=get_headers(), json=payload)
    if create_resp.status_code not in (201,):
        return jsonify({"error": "Failed to create repo", "detail": create_resp.text}), 500
    repo_info = create_resp.json()
    clone_url = repo_info.get("clone_url")

    # Setup local folder and initial commit & push
    try:
        local_path = init_local_repo_and_push(clone_url, name)
        return jsonify({"ok": True, "msg": "Repo created and pushed", "local_path": str(local_path)})
    except Exception as e:
        return jsonify({"error": "Repo created remotely but failed local setup", "detail": str(e)}), 500

def clone_or_pull_local_repo(clone_url, name):
    local_path = PROJECTS_DIR / name
    if local_path.exists():
        # pull latest
        subprocess.check_call(["git", "-C", str(local_path), "pull"])
    else:
        subprocess.check_call(["git", "clone", clone_url, str(local_path)])
    return local_path

def init_local_repo_and_push(clone_url, name):
    local_path = PROJECTS_DIR / name
    if local_path.exists():
        # if exists, attempt pull
        subprocess.check_call(["git", "-C", str(local_path), "pull"])
        return local_path

    local_path.mkdir(parents=True, exist_ok=False)
    # create README and initial commit
    (local_path / "README.md").write_text(f"# {name}\n\nCreated by n8n_manager\n")
    # Init git, add, commit
    subprocess.check_call(["git", "-C", str(local_path), "init"])
    subprocess.check_call(["git", "-C", str(local_path), "add", "."])
    subprocess.check_call(["git", "-C", str(local_path), "commit", "-m", "Initial commit from n8n_manager"],)
    # Add remote using token embedded URL for push (safer to use credential helper but this is simple)
    token = os.getenv("GITHUB_TOKEN","")
    username = os.getenv("GITHUB_USERNAME","")
    if not token or not username:
        raise RuntimeError("GITHUB_TOKEN or GITHUB_USERNAME not set")
    # Use https remote with token to push
    # Format: https://{token}@github.com/{username}/{repo}.git
    remote_url = f"https://{token}@github.com/{username}/{name}.git"
    subprocess.check_call(["git", "-C", str(local_path), "remote", "add", "origin", remote_url])
    subprocess.check_call(["git", "-C", str(local_path), "branch", "-M", "main"])
    subprocess.check_call(["git", "-C", str(local_path), "push", "-u", "origin", "main"])
    return local_path

@app.route("/api/sync_local", methods=["POST"])
def api_sync_local():
    """
    Ensure all remote repos have a local folder (clone if not).
    """
    refresh_env_values()
    resp = requests.get(urljoin(GITHUB_API, "user/repos"), headers=get_headers(), params={"per_page": 100})
    if resp.status_code != 200:
        return jsonify({"error": "GitHub API error", "detail": resp.text}), 500
    repos = resp.json()
    results = []
    for r in repos:
        name = r.get("name")
        clone_url = r.get("clone_url")
        try:
            local = clone_or_pull_local_repo(clone_url, name)
            results.append({"name": name, "local": str(local)})
        except Exception as e:
            results.append({"name": name, "error": str(e)})
    return jsonify({"ok": True, "results": results})

@app.route("/api/install_n8n", methods=["POST"])
def api_install_n8n():
    """
    Install n8n globally using npm. This runs synchronously and can take a while.
    """
    try:
        # Verify npm present
        subprocess.check_call(["node", "--version"])
        subprocess.check_call(["npm", "--version"])
    except Exception as e:
        return jsonify({"error": "Node.js / npm not found. Install Node.js and npm first.", "detail": str(e)}), 400

    try:
        # install n8n globally
        subprocess.check_call(["npm", "install", "-g", "n8n"])
        return jsonify({"ok": True, "msg": "n8n installed (npm install -g n8n) succeeded"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "npm install failed", "detail": str(e)}), 500

@app.route("/api/start_n8n", methods=["POST"])
def api_start_n8n():
    """
    Start n8n in a subprocess (foreground). The process will be launched and backgrounded using nohup-like method.
    """
    port = request.json.get("port", os.getenv("N8N_PORT", "5678"))
    try:
        # We'll attempt a simple nohup background start (works on Linux/mac)
        logfile = ROOT / "n8n_stdout.log"
        # Use setsid to detach process; on Windows this won't work the same way.
        cmd = f"n8n start --tunnel=false --port={port} &> {logfile} &"
        subprocess.check_call(cmd, shell=True, executable="/bin/bash")
        return jsonify({"ok": True, "msg": f"n8n start command issued on port {port}. Check {logfile} for logs."})
    except Exception as e:
        return jsonify({"error": "Failed to start n8n", "detail": str(e)}), 500

@app.route("/api/stop_n8n", methods=["POST"])
def api_stop_n8n():
    # Very simple stop approach: kill processes named n8n
    try:
        subprocess.check_call(["pkill", "-f", "n8n"])
        return jsonify({"ok": True, "msg": "Sent kill signal to n8n processes (if any)."})
    except Exception as e:
        return jsonify({"error": "Failed to stop n8n or none running", "detail": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", DEFAULT_PORT))
    app.run(host="0.0.0.0", port=port, debug=True)
