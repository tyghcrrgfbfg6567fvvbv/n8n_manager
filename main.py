from flask import Flask, render_template, request, jsonify
import os
import subprocess
import requests
from dotenv import load_dotenv
import threading
import json

app = Flask(__name__)
load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
N8N_PORT = os.getenv("N8N_PORT", "5678")
PROJECT_DIR = os.path.join(os.getcwd(), "project")

if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)

n8n_process = None

# 🔹 Get projects from GitHub repo
def get_projects():
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/project"
    try:
        response = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
        response.raise_for_status()
        # We only care about directories
        return [item for item in response.json() if item['type'] == 'dir']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching projects from GitHub: {e}")
        # If the directory doesn't exist, return empty list
        return []

# 🔹 Create project locally + on GitHub
def create_project_folder(name):
    # Create a .gitkeep file in the project folder on GitHub to ensure the folder is tracked
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/project/{name}/.gitkeep"
    data = {
        "message": f"Create project folder for {name}",
        "content": "" # Empty content, base64 encoded by default by requests
    }
    try:
        response = requests.put(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN), json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error creating project folder on GitHub: {e}")
        # Decide if we should still create locally. For now, we will.
    
    # Create local project folder
    path = os.path.join(PROJECT_DIR, name)
    if not os.path.exists(path):
        os.makedirs(path)

# 🔹 Install n8n if missing
def ensure_n8n_installed():
    try:
        subprocess.check_output(["n8n", "--version"], stderr=subprocess.STDOUT)
        print("n8n is already installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("n8n not found, attempting to install...")
        try:
            subprocess.check_call(["npm", "install", "-g", "n8n"])
            print("n8n installed successfully.")
            return True
        except Exception as e:
            print(f"Failed to install n8n: {e}")
            return False

# 🔹 Start n8n in background
def start_n8n():
    global n8n_process
    if n8n_process and n8n_process.poll() is None:
        return

    def run():
        global n8n_process
        # Note: In a real-world scenario, you'd want to manage the n8n database
        # on a per-project basis by setting the N8N_USER_FOLDER env var.
        # For this simplified example, we use one global n8n instance.
        cmd = ["n8n", "start", f"--port={N8N_PORT}"]
        n8n_process = subprocess.Popen(cmd)

    t = threading.Thread(target=run, daemon=True)
    t.start()

@app.route("/")
def index():
    # The frontend will fetch projects from the API, but we can pass the port
    return render_template("index.html", port=N8N_PORT)

@app.route("/api/create_project", methods=["POST"])
def create_project_route():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Project name required"}), 400

    create_project_folder(name)
    return jsonify({"success": True, "name": name})

@app.route("/api/projects")
def projects_route():
    projects = get_projects()
    return jsonify({"projects": projects})

@app.route("/api/env")
def env():
    return jsonify({
        "GITHUB_USERNAME": GITHUB_USERNAME,
        "GITHUB_REPO": GITHUB_REPO,
        "N8N_PORT": N8N_PORT
    })
    
@app.route("/api/sync_local", methods=["POST"])
def sync_local():
    projects = get_projects()
    synced_count = 0
    for project in projects:
        path = os.path.join(PROJECT_DIR, project["name"])
        if not os.path.exists(path):
            os.makedirs(path)
            synced_count += 1
    return jsonify({"success": True, "projects_synced": synced_count})

@app.route("/api/install_n8n", methods=["POST"])
def install_n8n_route():
    installed = ensure_n8n_installed()
    if installed:
        return jsonify({"success": True, "msg": "n8n installed successfully or already installed."})
    else:
        return jsonify({"success": False, "msg": "Failed to install n8n."})

@app.route("/api/start_n8n", methods=["POST"])
def start_n8n_route():
    start_n8n()
    return jsonify({"success": True, "msg": "n8n starting..."})


@app.route("/api/stop_n8n", methods=["POST"])
def stop_n8n():
    global n8n_process
    if n8n_process:
        n8n_process.terminate()
        n8n_process = None
        return jsonify({"success": True, "msg": "n8n stopped"})
    return jsonify({"success": False, "msg": "n8n not running"})

if __name__ == "__main__":
    ensure_n8n_installed()
    start_n8n()
    # Get port from environment variable, default to 5000 for local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)