/* Small UI behaviours: refresh, optional auto-refresh, log filtering. */
(() => {
  "use strict";
  const AUTO_KEY = "elt-dashboard-auto-refresh";
  const button = document.getElementById("refresh-report");
  const status = document.getElementById("refresh-status");
  const auto = document.getElementById("auto-refresh");

  function reload() {
    if (button) { button.disabled = true; button.textContent = "Refreshing…"; }
    if (status) status.textContent = "Reading the latest logs and storage state…";
    location.reload();
  }
  if (button) button.addEventListener("click", reload);

  let timer = null;
  function setAuto(on) {
    clearInterval(timer);
    if (on) timer = setInterval(reload, 30000);
    try { localStorage.setItem(AUTO_KEY, on ? "1" : "0"); } catch (e) { /* storage unavailable */ }
  }
  if (auto) {
    let saved = false;
    try { saved = localStorage.getItem(AUTO_KEY) === "1"; } catch (e) { /* ignore */ }
    auto.checked = saved;
    setAuto(saved);
    auto.addEventListener("change", () => setAuto(auto.checked));
  }

  /* Log viewer: level chips + text search. */
  const lines = [...document.querySelectorAll(".log-line")];
  if (lines.length) {
    const chips = [...document.querySelectorAll("[data-level]")];
    const search = document.getElementById("log-search");
    const count = document.getElementById("log-count");
    const apply = () => {
      const active = new Set(chips.filter((c) => c.getAttribute("aria-pressed") === "true").map((c) => c.dataset.level));
      const q = (search && search.value || "").trim().toLowerCase();
      let shown = 0;
      lines.forEach((li) => {
        const ok = active.has(li.dataset.level) && (!q || li.textContent.toLowerCase().includes(q));
        li.hidden = !ok;
        if (ok) shown++;
      });
      if (count) count.textContent = `${shown} of ${lines.length} events shown`;
    };
    chips.forEach((c) => c.addEventListener("click", () => {
      c.setAttribute("aria-pressed", c.getAttribute("aria-pressed") === "true" ? "false" : "true");
      apply();
    }));
    if (search) search.addEventListener("input", apply);
    apply();
  }
})();
