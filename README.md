# n8n Project Manager

A **Flask-based web interface** to manage **n8n projects** locally, with **GitHub as a database**. This tool allows you to create projects, list them, and launch n8n automatically inside a browser interface.

---

## Features

* ✅ Create a new project folder locally and automatically on GitHub
* ✅ List existing projects from the local `/project/` folder
* ✅ Launch n8n automatically in a browser iframe
* ✅ Install n8n if it’s missing (`npm install -g n8n`)
* ✅ Start n8n automatically in the background
* ✅ GitHub acts as a "database" for project storage
* ✅ Simple, clean web interface with top-left create button and top-right project menu

---

## Folder Structure

```
n8n_manager/
│
├── main.py                  # Flask backend
├── .env                     # GitHub username, token, repo, n8n port
├── templates/
│   └── index.html           # Frontend HTML
├── static/
│   ├── style.css            # Styles
│   └── script.js            # Frontend JS
└── project/                 # Local projects folder (auto-created)
```

---

## Environment Variables

Create a `.env` file in the root directory:

```env
GITHUB_USERNAME=YourGitHubUsername
GITHUB_TOKEN=ghp_yourtoken
GITHUB_REPO=n8n_manage
N8N_PORT=5678
```

* **GITHUB_USERNAME** → Your GitHub username
* **GITHUB_TOKEN** → GitHub personal access token with `repo` permissions
* **GITHUB_REPO** → Repository where project folders will be stored
* **N8N_PORT** → Port to run n8n (default: 5678)

---

## Installation

1. Make sure **Python 3.8+** is installed
2. Make sure **Node.js + npm** is installed
3. Install Python dependencies:

```bash
pip install flask python-dotenv requests
```

4. Clone or download this repository

---

## Usage

1. Start the Flask app:

```bash
python main.py
```

2. Open in browser: [http://localhost:5000](http://localhost:5000)

---

### Web Interface

* **Top-left ➕ button** → Create new project

  * Prompts for project name
  * Creates folder locally inside `/project/`
  * Pushes `.gitkeep` to GitHub inside `/project/<project_name>/`

* **Top-right ☰ button** → List existing projects

  * Click a project to open **n8n** in iframe

* **Workspace area** → Shows **n8n** interface for workflow management

* **Footer** → Shows number of local projects & n8n port

---

### n8n Management

* The script **checks if n8n is installed** when the app loads
* If missing → installs it via:

```bash
npm install -g n8n
```

* **Starts n8n automatically** in the background on the port defined in `.env`
* If n8n is already running → it won’t start a new instance

---

### GitHub Integration

* When a project is created, the backend automatically creates a folder in your GitHub repository:

```
/project/<project_name>/.gitkeep
```

* GitHub acts as a “database” to store project names
* Local `/project/` folder remains the primary working directory

---

### Folder Explanation

* `/project/` → Local project folders
* `/templates/index.html` → Frontend HTML
* `/static/style.css` → CSS styles
* `/static/script.js` → Handles button actions, prompts, AJAX calls to backend
* `main.py` → Flask backend API + n8n management

---

## API Endpoints

| Endpoint          | Method | Description                                   |
| ----------------- | ------ | --------------------------------------------- |
| `/`               | GET    | Load main web page                            |
| `/projects`       | GET    | List all local projects                       |
| `/create_project` | POST   | Create new project folder locally & on GitHub |
| `/stop_n8n`       | POST   | Stop the n8n background process               |

---

## Notes

* The workspace currently **shares a single n8n instance**.
* Each project can be opened in the same iframe; separate instances per project can be implemented in future updates.
* GitHub `.gitkeep` files are used to ensure folders are tracked, even if empty.

---

## Run Commands

# Start the Flask server
```bash
python main.py
```

# Open browser at
```bash
http://localhost:5000
```

---

## Future Improvements

* Separate n8n instance per project (with individual database folder)
* Add delete/rename project functionality
* Use GitHub Actions to sync changes automatically
* Add workflow template import/export

