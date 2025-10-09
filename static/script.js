document.addEventListener("DOMContentLoaded", () => {
  const reposContainer = document.getElementById("repos-container");
  const top3Div = document.getElementById("top-3");
  const newBtn = document.getElementById("new-project-btn");
  const modal = document.getElementById("modal");
  const cancelBtn = document.getElementById("cancel");
  const createBtn = document.getElementById("create-repo");
  const newNameInput = document.getElementById("new-name");
  const newPrivate = document.getElementById("new-private");
  const newDesc = document.getElementById("new-desc");
  const syncBtn = document.getElementById("sync-local");
  const installBtn = document.getElementById("install-n8n");
  const startBtn = document.getElementById("start-n8n");
  const stopBtn = document.getElementById("stop-n8n");
  const envInfo = document.getElementById("env-info");

  async function fetchEnv(){
    const res = await fetch("/api/env");
    const j = await res.json();
    envInfo.innerHTML = `<pre style="white-space:pre-wrap">${JSON.stringify(j, null, 2)}</pre>`;
  }

  async function loadRepos(){
    reposContainer.innerHTML = "Loading...";
    const res = await fetch("/api/repos");
    if (!res.ok) {
      reposContainer.innerHTML = "<div style='color:tomato'>Failed to load repos. Check .env token.</div>";
      return;
    }
    const data = await res.json();
    const repos = data.repos || [];
    // top 3
    top3Div.innerHTML = repos.slice(0,3).map(r => `<div>${r.name} — <span style="color:#9ca3af">${r.updated_at}</span></div>`).join("");
    reposContainer.innerHTML = "";
    if (repos.length===0) reposContainer.innerHTML = "<div style='color:var(--muted)'>No repositories found.</div>";
    for (let r of repos){
      const card = document.createElement("div");
      card.className = "repo-card";
      card.innerHTML = `<h4>${r.name}</h4>
        <div class="meta">${r.full_name} • ${r.private? "private":"public"}</div>
        <div style="margin-top:8px"><a target="_blank" href="${r.html_url}">Open on GitHub</a>
        <button data-repo="${r.name}" class="sync-btn" style="margin-left:8px">Sync</button></div>`;
      reposContainer.appendChild(card);
    }
    // attach sync button handlers
    document.querySelectorAll(".sync-btn").forEach(btn=>{
      btn.addEventListener("click", async (ev)=>{
        const name = btn.dataset.repo;
        btn.textContent = "Syncing...";
        btn.disabled = true;
        const resp = await fetch("/api/create", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name})});
        const j = await resp.json();
        alert(JSON.stringify(j));
        btn.textContent = "Sync";
        btn.disabled = false;
      });
    });
  }

  newBtn.addEventListener("click", ()=> modal.classList.remove("hidden"));
  cancelBtn.addEventListener("click", ()=> {
    modal.classList.add("hidden");
    newNameInput.value = ""; newDesc.value=""; newPrivate.checked=false;
  });

  createBtn.addEventListener("click", async ()=>{
    const name = newNameInput.value.trim();
    if (!name){ alert("Enter a repo name"); return; }
    createBtn.disabled = true;
    createBtn.textContent = "Creating...";
    const payload = {name, private: newPrivate.checked, description: newDesc.value||""};
    const resp = await fetch("/api/create", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    const j = await resp.json();
    alert(JSON.stringify(j));
    createBtn.disabled = false;
    createBtn.textContent = "Create";
    modal.classList.add("hidden");
    newNameInput.value=""; newDesc.value=""; newPrivate.checked=false;
    loadRepos();
  });

  syncBtn.addEventListener("click", async ()=>{
    syncBtn.disabled = true; syncBtn.textContent = "Syncing...";
    const resp = await fetch("/api/sync_local", {method:"POST"});
    const j = await resp.json();
    alert(JSON.stringify(j));
    syncBtn.disabled = false; syncBtn.textContent = "Sync all repos locally";
  });

  installBtn.addEventListener("click", async ()=>{
    if (!confirm("Install n8n globally using npm? This may take several minutes.")) return;
    installBtn.disabled = true; installBtn.textContent = "Installing...";
    const resp = await fetch("/api/install_n8n", {method:"POST"});
    const j = await resp.json();
    alert(JSON.stringify(j));
    installBtn.disabled = false; installBtn.textContent = "Install n8n";
  });

  startBtn.addEventListener("click", async ()=>{
    startBtn.disabled = true; startBtn.textContent = "Starting...";
    const resp = await fetch("/api/start_n8n", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({port:5678})});
    const j = await resp.json();
    alert(JSON.stringify(j));
    startBtn.disabled = false; startBtn.textContent = "Start n8n";
  });

  stopBtn.addEventListener("click", async ()=>{
    stopBtn.disabled = true; stopBtn.textContent = "Stopping...";
    const resp = await fetch("/api/stop_n8n", {method:"POST"});
    const j = await resp.json();
    alert(JSON.stringify(j));
    stopBtn.disabled = false; stopBtn.textContent = "Stop n8n";
  });

  // initial load
  fetchEnv();
  loadRepos();
});
