# n8n Project Manager

A **Flask-based web interface** to manage **n8n projects** locally, with a **single GitHub repository** acting as a central database for project structures. This tool allows you to create projects, list them, and launch a shared n8n instance in a browser interface.

---

## Features

* ✅ Create a new project folder locally and on GitHub within a single repository.
* ✅ List existing projects from the specified GitHub repository.
* ✅ Launch n8n in a dedicated workspace iframe.
* ✅ Install n8n if it’s missing (`npm install -g n8n`).
* ✅ Start and stop the n8n background process from the UI.
* ✅ Simple, clean two-column interface.

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
└── project/                 # Local projects folder (synced from GitHub)
```

---

## Environment Variables

Create a `.env` file in the root directory:

```env
GITHUB_USERNAME=YourGitHubUsername
GITHUB_TOKEN=ghp_yourtoken
GITHUB_REPO=your-repo-name
N8N_PORT=5678
```

* **GITHUB_USERNAME** → Your GitHub username.
* **GITHUB_TOKEN** → GitHub personal access token with `repo` permissions.
* **GITHUB_REPO** → The single repository where project folders will be stored (e.g., `n8n-projects`).
* **N8N_PORT** → Port to run n8n on (default: 5678).

---

## Installation

1. Make sure **Python 3.8+** and **Node.js + npm** are installed.
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Create the `.env` file as described above.
4. In your chosen GitHub repository, create an empty folder named `project`.

---

## Usage

1. Start the Flask app:

```bash
python main.py
```

2. Open in browser: [http://localhost:5000](http://localhost:5000)

---

### Web Interface

* **Left Panel (Projects)**:
    * Lists all project folders found in the `project/` directory of your GitHub repo.
    * Click a project to load the n8n UI in the workspace.
    * A **`+` button** at the top-right allows you to create a new project.
    * A **`Sync Projects Locally` button** ensures your local `/project/` directory matches the structure on GitHub.

* **Right Panel (Workspace)**:
    * An iframe that displays the n8n UI.

* **Bottom Panel (Controls)**:
    * Shows the environment variables loaded by the app.
    * Provides buttons to install, start, or stop the n8n service.

---

### n8n Management

* The script **checks if n8n is installed** when the app loads.
* If missing, you can install it via the **`Install n8n`** button.
* The **`Start n8n`** button runs n8n in the background on the port defined in `.env`.

---

### GitHub Integration

* When a project is created, the backend creates a folder in your specified GitHub repository by pushing an empty `.gitkeep` file to `project/<project_name>/.gitkeep`.
* This makes GitHub the source of truth for the project list.
* The local `/project/` folder is a mirror of the structure on GitHub, which you can sync at any time.

---

## API Endpoints

| Endpoint             | Method | Description                                      |
| -------------------- | ------ | ------------------------------------------------ |
| `/`                  | GET    | Load main web page                               |
| `/api/projects`      | GET    | List all projects from the GitHub repo.          |
| `/api/create_project`| POST   | Create a new project folder on GitHub & locally. |
| `/api/sync_local`    | POST   | Sync GitHub project structure to local folder.   |
| `/api/install_n8n`   | POST   | Trigger the installation of n8n.                 |
| `/api/start_n8n`     | POST   | Start the n8n background process.                |
| `/api/stop_n8n`      | POST   | Stop the n8n background process.                 |

---

## Notes

* The workspace currently **shares a single n8n instance**. Workflows are not isolated between projects in this version.
* Ensure the `project/` folder exists in your GitHub repository before running the application.

