// The config editor and the activity-log views.

import { $, el } from "./dom.js";
import { body, setStatus, state } from "./state.js";
import {
  clearLog,
  getLog,
  loadConfig,
  resetConfig,
  saveConfig,
} from "./api.js";
import { buildControls, buildSide } from "./chrome.js";

export function showConfig() {
  const c = state.cfg[state.planner];
  body.innerHTML = "";
  const ta = el("textarea", { spellcheck: false });
  ta.value = c.yaml;
  const err = el("div", { className: "cfg-err" });
  const note = el(
    "span",
    { style: "font-size:12px;color:var(--mut)" },
    c.from_template ? `${c.path} - from template (not yet saved)` : c.path,
  );
  const save = el("button", { className: "primary" }, "Save");
  const flash = el("span", { style: "font-size:12px;color:#2e7d32" });
  const reset = el(
    "button",
    { className: "danger", style: "margin-left:auto" },
    "Reset to template…",
  );
  ta.addEventListener("input", () => (flash.textContent = ""));
  save.onclick = async () => {
    const r = await saveConfig(state.planner, ta.value);
    if (r.ok) {
      err.textContent = "";
      flash.textContent = "saved ✓";
      note.textContent = c.path;
      setStatus("saved ✓");
      await loadConfig(state.planner);
      buildControls();
      buildSide();
    } else err.textContent = r.error || "save failed";
  };
  reset.onclick = () => {
    err.innerHTML = "";
    const yes = el("button", { className: "danger" }, "Confirm reset");
    const no = el("button", {}, "Cancel");
    no.onclick = () => (err.textContent = "");
    yes.onclick = async () => {
      const r = await resetConfig(state.planner);
      if (r.error) {
        err.textContent = r.error;
        return;
      }
      state.cfg[state.planner] = r;
      showConfig();
      buildControls();
      buildSide();
      setStatus(
        r.backup ? `reset - backup saved as ${r.backup}` : "reset to template",
      );
    };
    const row = el("div", {
      style: "display:flex; align-items:center; gap:8px",
    });
    row.append(
      el(
        "span",
        { style: "flex:1" },
        `Discard your ${state.planner} config and replace it with the template? A timestamped .bak is written first.`,
      ),
      yes,
      no,
    );
    err.append(row);
  };
  const wrap = el("div", { className: "cfg" });
  wrap.append(el("div", { className: "bar" }, ""), ta, err);
  $(".bar", wrap).append(save, flash, note, reset);
  body.append(wrap);
}

export async function showLog() {
  const s = await getLog();
  body.innerHTML = "";
  const wrap = el("div", { className: "sched" });
  wrap.append(
    el(
      "div",
      { className: "sched-head" },
      "<h1>Log</h1><p>Every render, export and wallpaper change - scheduled or manual. Live previews aren't logged.</p>",
    ),
  );

  const err = el("div", { className: "cfg-err" });
  const clear = el("button", { className: "danger" }, "Clear log…");
  clear.onclick = () => {
    err.innerHTML = "";
    const yes = el("button", { className: "danger" }, "Confirm clear");
    const no = el("button", {}, "Cancel");
    no.onclick = () => (err.textContent = "");
    yes.onclick = async () => {
      await clearLog();
      showLog();
    };
    const row = el("div", {
      style: "display:flex; align-items:center; gap:8px",
    });
    row.append(
      el(
        "span",
        { style: "flex:1" },
        "Clear the entire activity log? This can't be undone.",
      ),
      yes,
      no,
    );
    err.append(row);
  };
  const bar = el("div", { className: "grp" });
  bar.append(clear);
  const pre = el("pre", {}, (s.log || []).join("\n") || "(nothing logged yet)");
  wrap.append(bar, err, pre);
  body.append(wrap);
  pre.scrollTop = pre.scrollHeight; // newest at the bottom, in view on open
}
