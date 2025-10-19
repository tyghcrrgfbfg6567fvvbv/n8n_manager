document.addEventListener("DOMContentLoaded", () => {
  const projectsContainer = document.getElementById("projects-container");
  const newBtn = document.getElementById("new-project-btn");
  const modal = document.getElementById("modal");
  const cancelBtn = document.getElementById("cancel");
  const createBtn = document.getElementById("create-project");
  const newNameInput = document.getElementById("new-name");
  const syncBtn = document.getElementById("sync-local");
  const installBtn = document.getElementById("install-n8n");
  const startBtn = document.getElementById("start-n8n");
  const stopBtn = document.getElementById("stop-n8n");
  const envInfo = document.getElementById("env-info");
  const n8nIframe = document.getElementById("n8n-iframe");
  const menuBtn = document.getElementById("menu-btn");
  const sidePanel = document.getElementById("side-panel");
  const closeSidePanelBtn = document.getElementById("close-side-panel-btn");
  const overlay = document.getElementById("overlay");

  let N8N_PORT = "5678";

  async function fetchEnv(){
    const res = await fetch("/api/env");
    const j = await res.json();
    N8N_PORT = j.N8N_PORT || "5678";
    envInfo.innerHTML = `<pre style="white-space:pre-wrap">${JSON.stringify(j, null, 2)}</pre>`;
  }

  async function loadProjects(){
    projectsContainer.innerHTML = "Loading...";
    const res = await fetch("/api/projects");
    if (!res.ok) {
      projectsContainer.innerHTML = "<div style='color:tomato'>Failed to load projects. Check .env variables and ensure the 'project' folder exists in your repo.</div>";
      return;
    }
    const data = await res.json();
    const projects = data.projects || [];
    
    projectsContainer.innerHTML = "";
    if (projects.length === 0) projectsContainer.innerHTML = "<div style='color:var(--muted)'>No projects found. Create one!</div>";
    
    for (let p of projects){
      const card = document.createElement("div");
      card.className = "project-card";
      card.innerHTML = `<h4>${p.name}</h4>`;
      card.addEventListener("click", () => {
        n8nIframe.src = `http://localhost:${N8N_PORT}`;
        document.querySelectorAll('.project-card').forEach(c => c.style.background = '');
        card.style.background = 'var(--accent)';
        closeSidePanel();
      });
      projectsContainer.appendChild(card);
    }
  }

  function openSidePanel() {
    document.body.classList.add("side-panel-open");
    overlay.classList.remove("hidden");
  }

  function closeSidePanel() {
    document.body.classList.remove("side-panel-open");
    overlay.classList.add("hidden");
  }

  menuBtn.addEventListener("click", openSidePanel);
  closeSidePanelBtn.addEventListener("click", closeSidePanel);
  overlay.addEventListener("click", closeSidePanel);

  newBtn.addEventListener("click", ()=> modal.classList.remove("hidden"));
  cancelBtn.addEventListener("click", ()=> {
    modal.classList.add("hidden");
    newNameInput.value = "";
  });

  createBtn.addEventListener("click", async ()=>{
    const name = newNameInput.value.trim();
    if (!name){ alert("Enter a project name"); return; }
    createBtn.disabled = true;
    createBtn.textContent = "Creating...";
    const payload = { name };
    const resp = await fetch("/api/create_project", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    const j = await resp.json();
    
    if (j.success) {
        alert("Project created successfully!");
    } else {
        alert("Error creating project: " + JSON.stringify(j));
    }

    createBtn.disabled = false;
    createBtn.textContent = "Create";
    modal.classList.add("hidden");
    newNameInput.value="";
    loadProjects();
  });

  syncBtn.addEventListener("click", async ()=>{
    syncBtn.disabled = true; syncBtn.textContent = "Syncing...";
    const resp = await fetch("/api/sync_local", {method:"POST"});
    const j = await resp.json();
    alert(`Sync complete. ${j.projects_synced || 0} new projects synced locally.`);
    syncBtn.disabled = false; syncBtn.textContent = "Sync Projects Locally";
  });

  installBtn.addEventListener("click", async ()=>{
    if (!confirm("Install n8n globally using npm? This may take several minutes.")) return;
    installBtn.disabled = true; installBtn.textContent = "Installing...";
    const resp = await fetch("/api/install_n8n", {method:"POST"});
    const j = await resp.json();
    alert(j.msg || JSON.stringify(j));
    installBtn.disabled = false; installBtn.textContent = "Install n8n";
  });

  startBtn.addEventListener("click", async ()=>{
    startBtn.disabled = true; startBtn.textContent = "Starting...";
    const resp = await fetch("/api/start_n8n", {method:"POST"});
    const j = await resp.json();
    alert(j.msg || JSON.stringify(j));
    startBtn.disabled = false; startBtn.textContent = "Start n8n";
    // Give n8n a moment to start before trying to load it
    setTimeout(() => {
        n8nIframe.src = `http://localhost:${N8N_PORT}`;
    }, 3000);
  });

  stopBtn.addEventListener("click", async ()=>{
    stopBtn.disabled = true; stopBtn.textContent = "Stopping...";
    const resp = await fetch("/api/stop_n8n", {method:"POST"});
    const j = await resp.json();
    alert(j.msg || JSON.stringify(j));
    stopBtn.disabled = false; stopBtn.textContent = "Stop n8n";
    n8nIframe.src = "about:blank";
  });

  // initial load
  fetchEnv();
  loadProjects();
});
