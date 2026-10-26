// Entry point: view switching, planner selection, header actions and the row-click shim.

import { $ } from "./dom.js";
import {
  actions,
  body,
  controls,
  LOADING_PANE,
  setStatus,
  side,
  state,
} from "./state.js";
import { loadConfig } from "./api.js";
import { params } from "./params.js";
import { preview } from "./preview.js";
import { buildControls, buildSide } from "./chrome.js";
import { showConfig, showLog } from "./views.js";
import { showSchedule } from "./schedule.js";
import { openWallpaperDialog } from "./wallpaper.js";

function refreshView() {
  const preview_ = state.view === "preview";
  // Preview/Config are per-planner; Schedule and Log are shared app-wide overlays, so their
  // per-planner chrome is hidden and whichever button opened the overlay becomes Back.
  const overlay = state.view === "schedule" || state.view === "log";
  side.classList.toggle("hidden", !preview_);
  $("#sideFold").classList.toggle("hidden", !preview_);
  controls.classList.toggle("hidden", !preview_);
  actions.classList.toggle("hidden", !preview_);
  $("#planner").classList.toggle("hidden", overlay);
  $("#view").classList.toggle("hidden", overlay);
  $("#schedBtn").textContent =
    state.view === "schedule" ? "← Back" : "Schedule";
  $("#logBtn").textContent = state.view === "log" ? "← Back" : "Log";
  $("#schedBtn").classList.toggle("hidden", state.view === "log");
  $("#logBtn").classList.toggle("hidden", state.view === "schedule");
  if (state.view === "preview") preview();
  else if (state.view === "config") showConfig();
  else if (state.view === "schedule") showSchedule();
  else showLog();
}

function wireActions() {
  const m = state.cfg[state.planner].meta;
  $("#exportBtn").textContent =
    state.planner === "year" ? "Export PNG" : "Export PDF";
  $("#exportBtn").onclick = () =>
    window.open("/api/export?" + params(), "_blank");
  const wp = m.wallpaper;
  $("#wpBtn").classList.toggle("hidden", !wp.available);
  $("#wpBtn").onclick = () => openWallpaperDialog(wp);
}

async function selectPlanner(planner) {
  state.planner = planner;
  $("#planner")
    .querySelectorAll("button")
    .forEach((b) => b.classList.toggle("on", b.dataset.planner === planner));
  if (!state.cfg[planner]) {
    setStatus("loading…");
    body.innerHTML = LOADING_PANE;
    await loadConfig(planner);
  }
  buildControls();
  buildSide();
  wireActions();
  refreshView();
}

function selectView(view) {
  state.view = view;
  $("#view")
    .querySelectorAll("button")
    .forEach((b) => b.classList.toggle("on", b.dataset.view === view));
  refreshView();
}

$("#planner")
  .querySelectorAll("button")
  .forEach((b) => (b.onclick = () => selectPlanner(b.dataset.planner)));
$("#view")
  .querySelectorAll("button")
  .forEach((b) => (b.onclick = () => selectView(b.dataset.view)));
const overlayToggle = (view) => () => {
  if (state.view === view) selectView(state.prevView);
  else {
    if (state.view !== "schedule" && state.view !== "log")
      state.prevView = state.view;
    selectView(view);
  }
};
$("#schedBtn").onclick = overlayToggle("schedule");
$("#logBtn").onclick = overlayToggle("log");
$(".brand").onclick = () => selectView("preview");

const fold = $("#sideFold");
const applyFold = (off) => {
  $("main").classList.toggle("side-off", off);
  fold.textContent = off ? "›" : "‹";
  fold.title = off ? "Show sidebar" : "Hide sidebar";
  fold.setAttribute("aria-label", fold.title);
};
applyFold(localStorage.getItem("tg-side") === "off");
fold.onclick = () => {
  const off = !$("main").classList.contains("side-off");
  localStorage.setItem("tg-side", off ? "off" : "on");
  applyFold(off);
};

// Day/night switch for the panel chrome itself (independent of the planners' own theme).
// Light by default; the choice persists in localStorage.
// Lucide `moon`: shown in light mode (click -> dark)
const MOON = `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>`;
// Lucide `sun`: shown in dark mode (click -> light)
const SUN = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>`;
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const btn = $("#themeBtn");
  btn.innerHTML = theme === "dark" ? SUN : MOON;
  btn.title = theme === "dark" ? "Switch to light" : "Switch to dark";
}
applyTheme(localStorage.getItem("tg-theme") || "light");
$("#themeBtn").onclick = () => {
  const next =
    document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("tg-theme", next);
  applyTheme(next);
};

// The embedded browser doesn't reliably toggle a checkbox on click, so rows carry
// data-toggle and their children are pointer-events:none: every click lands on the
// row and we drive the checkbox here. (INPUT target means a keyboard space already did.)
document.addEventListener("click", (e) => {
  const row = e.target.closest("[data-toggle]");
  if (!row || e.target.tagName === "INPUT") return;
  const input = document.getElementById(row.dataset.toggle);
  if (input.disabled) return;
  input.checked = !input.checked;
  input.dispatchEvent(new Event("change", { bubbles: true }));
});

(async () => {
  await selectPlanner("weekly");
  selectView("preview");
})();
