// language: JavaScript, file: static/app.js
(() => {
  const PALETTES = ["sunset","mint","ink","acid","paper","royal","candy","steel"];
  const $ = s => document.querySelector(s);

  // theme persistence
  const saved = localStorage.getItem("tt-theme");
  if (saved) document.documentElement.dataset.theme = saved;
  const savedDensity = localStorage.getItem("tt-density");
  if (savedDensity) document.documentElement.dataset.density = savedDensity;

  const picker = $("#theme-picker");
  if (picker) {
    PALETTES.forEach(p => {
      const b = document.createElement("button");
      b.className = "dot";
      b.dataset.themeSet = p;
      b.style.background = getComputedStyle(document.documentElement).getPropertyValue(
        p === "sunset" ? "--accent" : "--accent") || "#000";
      b.onclick = () => setTheme(p);
      picker.appendChild(b);
    });
  }

  function setTheme(name) {
    document.documentElement.dataset.theme = name;
    localStorage.setItem("tt-theme", name);
    document.querySelectorAll("[data-theme-set]").forEach(el => {
      el.classList.toggle("on", el.dataset.themeSet === name);
    });
  }
  function setDensity(name) {
    document.documentElement.dataset.density = name;
    localStorage.setItem("tt-density", name);
  }

  document.querySelectorAll("[data-theme-set]").forEach(el => {
    el.classList.toggle("on", el.dataset.themeSet === document.documentElement.dataset.theme);
    el.addEventListener("click", () => setTheme(el.dataset.themeSet));
  });
  document.querySelectorAll("[data-density-set]").forEach(el => {
    el.addEventListener("click", () => setDensity(el.dataset.densitySet));
  });

  // home page logic
  const urlEl = $("#url");
  if (!urlEl) return;
  const goEl = $("#go"), statusEl = $("#status"), resultEl = $("#result");
  const thumbEl = $("#thumb"), titleEl = $("#title");
  const authorEl = $("#author"), sourceEl = $("#source"), durEl = $("#dur");
  const sourcesEl = $("#sources"), dlEl = $("#dl"), copyEl = $("#copy"), againEl = $("#again");
  let currentUrl = "", currentTitle = "";

  const setStatus = (msg, kind = "") => {
    statusEl.textContent = msg;
    statusEl.className = "status " + kind;
  };
  const fmtDur = s => !s ? "—" : `${Math.floor(s/60)}:${String(s%60).padStart(2,"0")}`;

  async function resolve() {
    const url = urlEl.value.trim();
    if (!url) return setStatus("URL kosong", "err");
    currentUrl = url;
    setStatus("RESOLVING…");
    resultEl.hidden = true;
    try {
      const r = await fetch("/api/resolve", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({url})
      });
      const j = await r.json();
      if (!j.ok) throw new Error((j.errors||[]).map(e=>e.join(": ")).join(" | ").slice(0,120));
      const d = j.data;
      currentTitle = d.title;
      thumbEl.src = d.thumbnail || "";
      titleEl.textContent = d.title || "—";
      authorEl.textContent = "@" + (d.author || "?");
      sourceEl.textContent = d.source;
      durEl.textContent = fmtDur(d.duration);
      sourcesEl.textContent = d.attempted.length ? `fallback: ${d.attempted.join(" → ")}` : "primary source";
      resultEl.hidden = false;
      setStatus("SIAP", "ok");
    } catch(e) {
      setStatus("GAGAL: " + e.message, "err");
    }
  }

  async function download() {
    if (!currentUrl) return setStatus("Resolve dulu", "err");
    setStatus("MENGUNDUH…");
    try {
      const r = await fetch("/api/download", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({url: currentUrl})
      });
      if (!r.ok) throw new Error((await r.text()).slice(0,100));
      const blob = await r.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = (currentTitle||"tiktok").replace(/[^\w\- ]/g,"_").slice(0,60)+".mp4";
      a.click();
      URL.revokeObjectURL(a.href);
      setStatus("SELESAI", "ok");
    } catch(e) {
      setStatus("UNDUH GAGAL: " + e.message, "err");
    }
  }

  goEl.addEventListener("click", resolve);
  urlEl.addEventListener("keydown", e => { if (e.key==="Enter") resolve(); });
  dlEl.addEventListener("click", download);
  copyEl.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(currentUrl); setStatus("URL TERSALIN","ok"); }
    catch { setStatus("COPY GAGAL","err"); }
  });
  againEl.addEventListener("click", () => {
    urlEl.value = ""; currentUrl = ""; resultEl.hidden = true; setStatus("");
    urlEl.focus();
  });

  setInterval(() => { const c = $("#clock"); if (c) c.textContent = new Date().toLocaleTimeString("id-ID",{hour12:false}); }, 1000);
})();
