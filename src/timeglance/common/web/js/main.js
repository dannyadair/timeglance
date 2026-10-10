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
