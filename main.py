from flask import Flask, render_template, request, jsonify
import os
import subprocess
import requests
from dotenv import load_dotenv
import threading

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

# 🔹 Get local projects
def get_local_projects():
    return [d for d in os.listdir(PROJECT_DIR) if os.path.isdir(os.path.join(PROJECT_DIR, d))]

# 🔹 Create project locally + GitHub
def create_project_folder(name):
    path = os.path.join(PROJECT_DIR, name)
    if not os.path.exists(path):
        os.makedirs(path)

    # GitHub: create folder by creating a dummy .gitkeep file
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/project/{name}/.gitkeep"
    data = {"message": f"Create project {name}", "content": ""}
    try:
        requests.put(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN), json=data)
    except:
        pass  # ignore GitHub errors

# 🔹 Install n8n if missing
def ensure_n8n_installed():
    try:
        subprocess.check_call(["n8n", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        try:
            subprocess.check_call(["npm", "install", "-g", "n8n"])
            return True
        except Exception as e:
            print("Failed to install n8n:", e)
            return False

# 🔹 Start n8n in background
def start_n8n():
    global n8n_process
    if n8n_process and n8n_process.poll() is None:
        return

    def run():
        global n8n_process
        cmd = ["n8n", "start", "--tunnel=false", f"--port={N8N_PORT}"]
        n8n_process = subprocess.Popen(cmd)

    t = threading.Thread(target=run, daemon=True)
    t.start()

@app.route("/")
def index():
    ensure_n8n_installed()
    start_n8n()
    projects = get_local_projects()
    return render_template("index.html", projects=projects, port=N8N_PORT)

@app.route("/create_project", methods=["POST"])
def create_project():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Project name required"}), 400

    create_project_folder(name)
    start_n8n()
    return jsonify({"success": True, "name": name})

@app.route("/projects")
def projects():
    return jsonify(get_local_projects())

@app.route("/stop_n8n", methods=["POST"])
def stop_n8n():
    global n8n_process
    if n8n_process:
        n8n_process.terminate()
        n8n_process = None
        return jsonify({"success": True, "msg": "n8n stopped"})
    return jsonify({"success": False, "msg": "n8n not running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
        
