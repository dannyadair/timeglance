const $ = (s, r = document) => r.querySelector(s);
const el = (tag, attrs = {}, html) => {
  const n = Object.assign(document.createElement(tag), attrs);
  if (html != null) n.innerHTML = html;
  return n;
};
const state = { planner: "weekly", view: "preview", prevView: "preview", cfg: {} };

const side = $("#side");
const body = $("#viewbody");
const controls = $("#controls");
const actions = $("#actions");
const status = $("#status");
const LOADING_PANE = '<div class="preview-pane loading"><div class="load-ov"><div class="spinner"></div></div></div>';

function setStatus(msg) {
  status.textContent = msg || "";
}

async function loadConfig(planner) {
  state.cfg[planner] = await fetch("/api/config?planner=" + planner).then((r) => r.json());
}

// ---- header controls (per planner) ----
function opt(values, current) {
  return values
    .map((v) => `<option value="${v}" ${v === current ? "selected" : ""}>${v || "(none)"}</option>`)
    .join("");
}

function buildControls() {
  const m = state.cfg[state.planner].meta;
  controls.innerHTML = "";
  if (state.planner === "year") {
    controls.append(
      grp("Theme", `<select id="c_theme">${opt(m.themes, m.theme)}</select>`),
      grp("Layout", `<select id="c_layout">${opt(m.layouts, m.layout)}</select>`),
      grp("Weeks", `<span data-toggle="c_align"><input type="checkbox" id="c_align" ${m.week_align ? "checked" : ""}><label>aligned</label></span>`),
      grp("Week", `<select id="c_week"><option ${m.week_start === "Mon" ? "selected" : ""}>Mon</option><option ${m.week_start === "Sun" ? "selected" : ""}>Sun</option></select>`),
      grp("Range", `<input class="range" id="c_start" value="${m.range.start}"> – <input class="range" id="c_end" value="${m.range.end}">`),
      grp("Size", `<select id="c_size">${opt(["", ...m.sizes], m.size)}</select>`),
    );
  } else {
    controls.append(grp("Paper", `<select id="c_paper">${opt(m.papers, m.paper)}</select>`));
  }
  controls
    .querySelectorAll("select, input")
    .forEach((c) => c.addEventListener(c.type === "checkbox" ? "change" : "input", preview));
  if (state.planner === "year") wireRangeHelp();
}

function grp(label, inner) {
  return el("span", { className: "grp" }, `<label>${label}</label>${inner}`);
}

let rangeHelpOff;

// Legend for the range date-notations. Pops up on its own while you work in the range fields;
// the × tucks it away so you can read what's underneath while still typing. It reappears when
// you re-enter a field and clears once you move on elsewhere.
function wireRangeHelp() {
  if (rangeHelpOff) rangeHelpOff();
  const start = $("#c_start");
  const end = $("#c_end");
  const pop = el("div", { className: "help-pop hidden" },
    `<span class="x">×</span><h4>Range notations (start / end month)</h4>
     <dl>
       <dt>2026</dt><dd>a whole year (Jan–Dec)</dd>
       <dt>2026-07</dt><dd>a specific month</dd>
       <dt>today</dt><dd>the current month</dd>
       <dt>today±N</dt><dd>N months from now, e.g. today-1, today+12</dd>
       <dt>year-start</dt><dd>January of the current year</dd>
       <dt>year-end</dt><dd>December of the current year</dd>
     </dl>`);
  start.parentElement.append(pop);
  const zone = [start, end, pop];
  const inZone = (t) => zone.some((z) => z === t || z.contains(t));
  let dismissed = false;
  const onFocus = (e) => {
    if (e.target === start || e.target === end) {
      if (!dismissed) pop.classList.remove("hidden");
    } else if (!inZone(e.target)) {
      dismissed = false;
      pop.classList.add("hidden");
    }
  };
  const onDown = (e) => {
    if (!inZone(e.target)) {
      dismissed = false;
      pop.classList.add("hidden");
    }
  };
  $(".x", pop).addEventListener("click", () => {
    dismissed = true;
    pop.classList.add("hidden");
  });
  document.addEventListener("focusin", onFocus);
  document.addEventListener("pointerdown", onDown);
  rangeHelpOff = () => {
    document.removeEventListener("focusin", onFocus);
    document.removeEventListener("pointerdown", onDown);
  };
}

// ---- sidebar (per planner) ----
function buildSide() {
  const m = state.cfg[state.planner].meta;
  side.innerHTML = "";
  side.append(el("h2", {}, state.planner === "year" ? "Layers" : "Activities"));
  for (const l of m.layers) {
    const id = "ly_" + l.id;
    const row = el("div", { className: "row" });
    row.dataset.toggle = id;
    row.innerHTML = `<input type="checkbox" id="${id}" data-layer value="${l.id}" ${l.visible ? "checked" : ""}>
      <label><span class="sw" style="background:${l.color}"></span>${l.label}</label>`;
    row.querySelector("input").addEventListener("change", preview);
    side.append(row);
  }
  if (state.planner !== "year") return;
  const byId = Object.fromEntries(m.layers.map((l) => [l.id, l.color]));
  side.append(el("h2", { style: "margin-top:16px" }, "Sources"));
  for (const s of m.sources) {
    const dot = s.layer ? `<span class="sw" style="background:${byId[s.layer] || "#ccc"}"></span>` : "";
    const cnt = s.error
      ? `<span class="cnt" style="color:#C4553B" title="${s.error}">⚠</span>`
      : `<span class="cnt">${s.count}</span>`;
    side.append(
      el("div", { className: "row src" },
        `<span class="kind">${s.kind}</span>${dot}<span class="lbl" title="${s.error || s.origin || ""}">${s.label}</span>${cnt}`),
    );
  }
}

// ---- params ----
function params() {
  const p = new URLSearchParams({ planner: state.planner });
  const hide = [...side.querySelectorAll("input[data-layer]:not(:checked)")].map((c) => c.value);
  p.set("hide", hide.join(","));
  if (state.planner === "year") {
    p.set("theme", $("#c_theme").value);
    p.set("layout", $("#c_layout").value);
    p.set("week_align", $("#c_align").checked);
    p.set("week_start", $("#c_week").value);
    if ($("#c_start").value) p.set("start", $("#c_start").value);
    if ($("#c_end").value) p.set("end", $("#c_end").value);
    if ($("#c_size").value) p.set("size", $("#c_size").value);
  } else {
    p.set("paper", $("#c_paper").value);
  }
  return p;
}

// ---- views ----
async function preview() {
  if (state.view !== "preview") return;
  setStatus("rendering…");
  body.innerHTML = LOADING_PANE;
  const pane = $(".preview-pane", body);
  const q = params();
  if (state.planner === "year") {
    const res = await fetch("/api/preview?" + q);
    pane.classList.remove("loading");
    if (res.ok) {
      pane.innerHTML = await res.text();
      setStatus("");
    } else {
      const msg = (await res.json()).error || "render failed";
      pane.append(el("div", { className: "pv-msg", textContent: msg }));
      setStatus(msg);
    }
  } else {
    const frame = el("iframe");
    frame.onload = () => {
      pane.classList.remove("loading");
      setStatus("");
    };
    frame.src = "/api/preview?" + q;
    pane.append(frame);
  }
}

function showConfig() {
  const c = state.cfg[state.planner];
  body.innerHTML = "";
  const ta = el("textarea", { spellcheck: false });
  ta.value = c.yaml;
  const err = el("div", { className: "cfg-err" });
  const note = el("span", { style: "font-size:12px;color:var(--mut)" },
    c.from_template ? `${c.path} - from template (not yet saved)` : c.path);
  const save = el("button", { className: "primary" }, "Save");
  const flash = el("span", { style: "font-size:12px;color:#2e7d32" });
  const reset = el("button", { className: "danger", style: "margin-left:auto" }, "Reset to template…");
  ta.addEventListener("input", () => (flash.textContent = ""));
  save.onclick = async () => {
    const r = await fetch("/api/config?planner=" + state.planner, { method: "POST", body: JSON.stringify({ yaml: ta.value }) }).then((r) => r.json());
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
      const r = await fetch("/api/config/reset?planner=" + state.planner, { method: "POST" }).then((r) => r.json());
      if (r.error) {
        err.textContent = r.error;
        return;
      }
      state.cfg[state.planner] = r;
      showConfig();
      buildControls();
      buildSide();
      setStatus(r.backup ? `reset - backup saved as ${r.backup}` : "reset to template");
    };
    const row = el("div", { style: "display:flex; align-items:center; gap:8px" });
    row.append(
      el("span", { style: "flex:1" },
        `Discard your ${state.planner} config and replace it with the template? A timestamped .bak is written first.`),
      yes, no,
    );
    err.append(row);
  };
  const wrap = el("div", { className: "cfg" });
  wrap.append(el("div", { className: "bar" }, ""), ta, err);
  $(".bar", wrap).append(save, flash, note, reset);
  body.append(wrap);
}

async function showSchedule() {
  const s = await fetch("/api/schedule").then((r) => r.json());
  body.innerHTML = "";
  const wrap = el("div", { className: "sched" });
  wrap.append(el("div", { className: "sched-head" },
    "<h1>Schedule</h1><p>Daily re-rendering of planners - write their files to disk, set them as desktop wallpaper.</p>"));

  const card = el("div", { className: "card" });
  card.append(
    el("div", { className: "grp", style: "margin-bottom:10px" },
      `<span class="dot ${s.running ? "on" : ""}"></span><strong>${s.running ? "Running" : "Stopped"}</strong>`),
    el("div", { className: "grp" },
      `<label>Daily at</label><input id="s_time" value="${s.time}" style="width:70px"><span class="hint">${s.tz}</span>`),
  );

  // What a run writes: each ticked planner re-renders to its file on disk.
  card.append(el("div", { className: "grp", style: "margin-top:10px" }, "<label>Writes</label>"));
  for (const [name, label] of [["year", "Year"], ["weekly", "Weekly"]]) {
    card.append(el("div", { className: "grp schd-pl", style: "margin-top:4px; padding-left:4px" },
      `<span data-toggle="s_${name}"><input type="checkbox" class="s-pl" id="s_${name}" value="${name}" ${s.planners.includes(name) ? "checked" : ""}><label>${label}</label></span>
       <code class="dst">→ ${s.outputs[name]}</code>`));
  }

  // The optional extra: also push each written file to the desktop as wallpaper.
  card.append(el("div", { className: "grp", style: "margin-top:12px" },
    `<label>Also</label><span data-toggle="s_wp"><input type="checkbox" id="s_wp" ${s.wallpaper ? "checked" : ""}><label>set as wallpaper</label></span>`));

  // Per-planner screen assignment: with >1 screen, each planner can target specific outputs
  // (e.g. weekly on the laptop, year on the ultrawide) instead of every planner claiming all.
  // All boxes ticked == "all" (sent as []), so a newly attached screen is still covered.
  const scrRow = (planner, label) => {
    const assigned = (s.screens && s.screens[planner]) || [];
    const row = el("div", { className: "grp", style: "margin-top:6px" }, `<label>${label}</label>`);
    for (const sc of s.wp_screens) {
      const id = `sc_${planner}_${sc.name}`;
      const on = assigned.length === 0 || assigned.includes(sc.name);
      const span = el("span", {}, `<input type="checkbox" class="schd-scr" data-planner="${planner}" id="${id}" value="${sc.name}" ${on ? "checked" : ""}><label>${sc.model || sc.name}</label>`);
      span.dataset.toggle = id;
      row.append(span);
    }
    return row;
  };
  if (s.wp_screens.length > 1) {
    card.append(el("div", { className: "grp", style: "margin-top:10px" }, "<label>Screens per planner</label>"), scrRow("year", "Year"), scrRow("weekly", "Weekly"));
  }

  const bar = el("div", { className: "grp", style: "margin-top:12px" });
  const start = el("button", { className: "primary" }, "Start");
  const stop = el("button", {}, "Stop");
  const runNow = el("button", {}, "Run now");
  bar.append(start, stop, runNow,
    el("span", { style: "font-size:12px;color:var(--mut)" },
      `${s.last_run ? "last " + s.last_run : ""}${s.next_run ? "  ·  next " + s.next_run : ""}`));
  card.append(bar);

  const collect = (action) => {
    const cfg = {
      time: $("#s_time").value,
      planners: [...card.querySelectorAll("input.s-pl:checked")].map((c) => c.value),
      wallpaper: $("#s_wp").checked,
      action,
    };
    if (s.wp_screens.length > 1) {
      cfg.screens = {};
      for (const t of ["year", "weekly"]) {
        const chosen = [...body.querySelectorAll(`input.schd-scr[data-planner="${t}"]:checked`)].map((c) => c.value);
        cfg.screens[t] = chosen.length === s.wp_screens.length ? [] : chosen;
      }
    }
    return cfg;
  };
  const post = async (action) => {
    await fetch("/api/schedule", { method: "POST", body: JSON.stringify(collect(action)) });
    showSchedule();
  };
  start.onclick = () => post("start");
  stop.onclick = () => post("stop");
  runNow.onclick = () => post("run");

  wrap.append(card);
  body.append(wrap);
}

async function showLog() {
  const s = await fetch("/api/log").then((r) => r.json());
  body.innerHTML = "";
  const wrap = el("div", { className: "sched" });
  wrap.append(el("div", { className: "sched-head" },
    "<h1>Log</h1><p>Every render, export and wallpaper change - scheduled or manual. Live previews aren't logged.</p>"));

  const err = el("div", { className: "cfg-err" });
  const clear = el("button", { className: "danger" }, "Clear log…");
  clear.onclick = () => {
    err.innerHTML = "";
    const yes = el("button", { className: "danger" }, "Confirm clear");
    const no = el("button", {}, "Cancel");
    no.onclick = () => (err.textContent = "");
    yes.onclick = async () => {
      await fetch("/api/log/clear", { method: "POST" });
      showLog();
    };
    const row = el("div", { style: "display:flex; align-items:center; gap:8px" });
    row.append(el("span", { style: "flex:1" }, "Clear the entire activity log? This can't be undone."), yes, no);
    err.append(row);
  };
  const bar = el("div", { className: "grp" });
  bar.append(clear);
  const pre = el("pre", {}, (s.log || []).join("\n") || "(nothing logged yet)");
  wrap.append(bar, err, pre);
  body.append(wrap);
  pre.scrollTop = pre.scrollHeight; // newest at the bottom, in view on open
}

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
  $("#schedBtn").textContent = state.view === "schedule" ? "← Back" : "Schedule";
  $("#logBtn").textContent = state.view === "log" ? "← Back" : "Log";
  $("#schedBtn").classList.toggle("hidden", state.view === "log");
  $("#logBtn").classList.toggle("hidden", state.view === "schedule");
  if (state.view === "preview") preview();
  else if (state.view === "config") showConfig();
  else if (state.view === "schedule") showSchedule();
  else showLog();
}

// ---- actions ----
function wireActions() {
  const m = state.cfg[state.planner].meta;
  $("#exportBtn").textContent = state.planner === "year" ? "Export PNG" : "Export PDF";
  $("#exportBtn").onclick = () => window.open("/api/export?" + params(), "_blank");
  const wp = m.wallpaper;
  $("#wpBtn").classList.toggle("hidden", !wp.available);
  $("#wpBtn").onclick = () => openWallpaperDialog(wp);
}

const FILLS = ["preserveAspectCrop", "preserveAspectFit", "stretch", "tile", "pad"];

// Which screens the YAML `wallpaper.screens` selects: "all" | "primary" | list of output names.
function wpSelected(sel, s) {
  if (!sel || sel === "all") return true;
  if (sel === "primary") return !!s.primary;
  const list = Array.isArray(sel) ? sel : String(sel).split(",").map((x) => x.trim());
  return list.includes(s.name);
}

function openWallpaperDialog(wp) {
  const bg = el("div", { className: "modal-bg" });
  const modal = el("div", { className: "modal" });
  const list = el("div");
  for (const s of wp.screens) {
    const model = s.model || (/^(eDP|LVDS)/i.test(s.name) ? "Built-in display" : s.name);
    const id = "wpscr_" + s.name;
    const row = el("div", { className: "scr" });
    row.dataset.toggle = id;
    const on = wpSelected(wp.selected, s);
    row.innerHTML = `<input type="checkbox" id="${id}" value="${s.name}" ${on ? "checked" : ""}>
      <label><span>${model}</span>
      <span class="res">${s.name} · ${s.w}×${s.h}${s.primary ? " · primary" : ""}</span></label>`;
    list.append(row);
  }
  const fill = el("select", {}, FILLS.map((f) => `<option ${f === wp.fill ? "selected" : ""}>${f}</option>`).join(""));
  const warn = el("div", { className: "warn" });
  const cancel = el("button", {}, "Cancel");
  const apply = el("button", { className: "primary" }, "Apply");
  const close = () => bg.remove();
  cancel.onclick = close;
  bg.onclick = (e) => e.target === bg && close();
  const busy = el("div", { className: "busy" }, '<span class="spinner-sm"></span>Setting wallpaper…');
  apply.onclick = async () => {
    const chosen = [...list.querySelectorAll("input:checked")].map((c) => c.value);
    if (!chosen.length) return (warn.textContent = "Select at least one screen.");
    warn.textContent = "";
    foot.replaceChildren(el("span", { className: "sp" }), busy);
    setStatus("setting wallpaper…");
    const b = { ...Object.fromEntries(params()), screens: chosen.join(","), fill: fill.value };
    const r = await fetch("/api/wallpaper?planner=" + state.planner, { method: "POST", body: JSON.stringify(b) }).then((x) => x.json());
    if (!r.ok) {
      warn.textContent = "Failed: " + (r.error || "");
      foot.replaceChildren(el("span", { className: "sp" }), cancel, apply);
      return;
    }
    close();
    setStatus(
      r.applied.length
        ? `wallpaper set ✓ on ${r.applied.join(", ")}`
        : `nothing applied - no Plasma desktop matched (detected: ${r.desktops.join(" ")})`,
    );
  };
  modal.append(
    el("h3", {}, "Set as wallpaper"),
    el("label", { style: "font-size:12px;color:var(--mut)" }, "Screens (rendered at current resolution)"),
    list,
    el("div", { className: "grp", style: "margin-top:10px" }, "<label>Fit</label>"),
    warn,
  );
  $(".grp", modal).append(fill);
  const foot = el("div", { className: "foot" });
  foot.append(el("span", { className: "sp" }), cancel, apply);
  modal.append(foot);
  bg.append(modal);
  document.body.append(bg);
}

async function selectPlanner(planner) {
  state.planner = planner;
  $("#planner").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.planner === planner));
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
  $("#view").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.view === view));
  refreshView();
}

$("#planner").querySelectorAll("button").forEach((b) => (b.onclick = () => selectPlanner(b.dataset.planner)));
$("#view").querySelectorAll("button").forEach((b) => (b.onclick = () => selectView(b.dataset.view)));
const overlayToggle = (view) => () => {
  if (state.view === view) selectView(state.prevView);
  else {
    if (state.view !== "schedule" && state.view !== "log") state.prevView = state.view;
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
  input.checked = !input.checked;
  input.dispatchEvent(new Event("change", { bubbles: true }));
});

(async () => {
  await selectPlanner("weekly");
  selectView("preview");
})();
