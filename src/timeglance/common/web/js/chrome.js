// Per-planner chrome: the header controls and the sidebar (layers/topics + year sources).

import { $, el } from "./dom.js";
import { controls, side, state } from "./state.js";
import { preview } from "./preview.js";

function opt(values, current) {
  return values
    .map(
      (v) =>
        `<option value="${v}" ${v === current ? "selected" : ""}>${v || "(none)"}</option>`,
    )
    .join("");
}

function grp(label, inner) {
  return el("span", { className: "grp" }, `<label>${label}</label>${inner}`);
}

export function buildControls() {
  const m = state.cfg[state.planner].meta;
  controls.innerHTML = "";
  if (state.planner === "year") {
    controls.append(
      grp("Theme", `<select id="c_theme">${opt(m.themes, m.theme)}</select>`),
      grp(
        "Layout",
        `<select id="c_layout">${opt(m.layouts, m.layout)}</select>`,
      ),
      grp(
        "Weeks",
        `<span data-toggle="c_align"><input type="checkbox" id="c_align" ${m.week_align ? "checked" : ""}><label>aligned</label></span>`,
      ),
      grp(
        "Week",
        `<select id="c_week"><option ${m.week_start === "Mon" ? "selected" : ""}>Mon</option><option ${m.week_start === "Sun" ? "selected" : ""}>Sun</option></select>`,
      ),
      grp(
        "Range",
        `<input class="range" id="c_start" value="${m.range.start}"> – <input class="range" id="c_end" value="${m.range.end}">`,
      ),
      grp(
        "Size",
        `<select id="c_size">${opt(["", ...m.sizes], m.size)}</select>`,
      ),
    );
  } else {
    controls.append(
      grp("Paper", `<select id="c_paper">${opt(m.papers, m.paper)}</select>`),
    );
  }
  controls
    .querySelectorAll("select, input")
    .forEach((c) =>
      c.addEventListener(c.type === "checkbox" ? "change" : "input", preview),
    );
  if (state.planner === "year") wireRangeHelp();
}

let rangeHelpOff;

// Legend for the range date-notations. Pops up on its own while you work in the range fields;
// the × tucks it away so you can read what's underneath while still typing. It reappears when
// you re-enter a field and clears once you move on elsewhere.
function wireRangeHelp() {
  if (rangeHelpOff) rangeHelpOff();
  const start = $("#c_start");
  const end = $("#c_end");
  const pop = el(
    "div",
    { className: "help-pop hidden" },
    `<span class="x">×</span><h4>Range notations (start / end month)</h4>
     <dl>
       <dt>2026</dt><dd>a whole year (Jan–Dec)</dd>
       <dt>2026-07</dt><dd>a specific month</dd>
       <dt>today</dt><dd>the current month</dd>
       <dt>today±N</dt><dd>N months from now, e.g. today-1, today+12</dd>
       <dt>year-start</dt><dd>January of the current year</dd>
       <dt>year-end</dt><dd>December of the current year</dd>
     </dl>`,
  );
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

export function buildSide() {
  const m = state.cfg[state.planner].meta;
  side.innerHTML = "";
  side.append(el("h2", {}, state.planner === "year" ? "Layers" : "Topics"));
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
    const dot = s.layer
      ? `<span class="sw" style="background:${byId[s.layer] || "#ccc"}"></span>`
      : "";
    const cnt = s.error
      ? `<span class="cnt" style="color:#C4553B" title="${s.error}">⚠</span>`
      : `<span class="cnt">${s.count}</span>`;
    side.append(
      el(
        "div",
        { className: "row src" },
        `<span class="kind">${s.kind}</span>${dot}<span class="lbl" title="${s.error || s.origin || ""}">${s.label}</span>${cnt}`,
      ),
    );
  }
}
