// The "Set as wallpaper" dialog: pick screens (incl. remembered-offline) and a fit mode.

import { $, el } from "./dom.js";
import { setStatus, state } from "./state.js";
import { params } from "./params.js";
import { forgetScreen, setWallpaper } from "./api.js";

// Plasma org.kde.image FillMode -> the label Plasma's own wallpaper dialog uses (ordered to match).
const FILLS = {
  preserveAspectCrop: "Scaled and cropped",
  stretch: "Scaled",
  preserveAspectFit: "Scaled, keep proportions",
  pad: "Centered",
  tile: "Tiled",
};

// Which screens the YAML `wallpaper.screens` selects: "all" | "primary" | list of output names.
// "all"/"primary" only pre-tick connected screens; a disconnected one is targeted only when named.
function wpSelected(sel, s) {
  if (!sel || sel === "all") return s.connected;
  if (sel === "primary") return !!s.primary;
  const list = Array.isArray(sel)
    ? sel
    : String(sel)
        .split(",")
        .map((x) => x.trim());
  return list.includes(s.name);
}

export function openWallpaperDialog(wp) {
  const bg = el("div", { className: "modal-bg" });
  const modal = el("div", { className: "modal" });
  const list = el("div");
  const sel = wp.selected;
  const selList = Array.isArray(sel)
    ? sel
    : sel && sel !== "all" && sel !== "primary"
      ? String(sel)
          .split(",")
          .map((x) => x.trim())
      : [];
  const names = new Set(wp.screens.map((s) => s.name));
  // config names we've never seen (bad id, or state cleared): FYI only, no resolution to render.
  const unseen = selList
    .filter((n) => !names.has(n))
    .map((n) => ({ name: n, connected: false, seen: false }));
  for (const s of [...wp.screens, ...unseen]) {
    const seen = s.seen !== false;
    const model =
      s.model || (/^(eDP|LVDS)/i.test(s.name) ? "Built-in display" : s.name);
    const id = "wpscr_" + s.name;
    const row = el("div", { className: "scr" });
    const toggle = el("div", { className: "scr-toggle" });
    toggle.dataset.toggle = id;
    const on = seen ? wpSelected(sel, s) : true;
    const detail = !seen
      ? `${s.name} · in config, never seen`
      : `${s.name} · ${s.w}×${s.h}${s.primary ? " · primary" : s.connected ? "" : ` · offline, seen ${s.last_seen}`}`;
    toggle.innerHTML = `<input type="checkbox" id="${id}" value="${s.name}" ${on ? "checked" : ""}>
      <label><span>${model}</span>
      <span class="res">${detail}</span></label>`;
    row.append(toggle);
    // A disconnected screen is still offered (its file is written now, applied on reconnect);
    // Forget drops a retired monitor from the registry. An unseen name isn't in the registry.
    if (!s.connected && seen) {
      const f = el(
        "button",
        { className: "forget", title: `Forget ${s.name}` },
        "Forget",
      );
      f.onclick = async () => {
        await forgetScreen(s.name);
        row.remove();
      };
      row.append(f);
    }
    list.append(row);
  }
  const fill = el(
    "select",
    {},
    Object.entries(FILLS)
      .map(
        ([v, label]) =>
          `<option value="${v}" ${v === wp.fill ? "selected" : ""}>${label}</option>`,
      )
      .join(""),
  );
  const warn = el("div", { className: "warn" });
  const cancel = el("button", {}, "Cancel");
  const apply = el("button", { className: "primary" }, "Apply");
  const close = () => bg.remove();
  cancel.onclick = close;
  bg.onclick = (e) => e.target === bg && close();
  const busy = el(
    "div",
    { className: "busy" },
    '<span class="spinner-sm"></span>Setting wallpaper…',
  );
  apply.onclick = async () => {
    const chosen = [...list.querySelectorAll("input:checked")].map(
      (c) => c.value,
    );
    if (!chosen.length)
      return (warn.textContent = "Select at least one screen.");
    warn.textContent = "";
    foot.replaceChildren(el("span", { className: "sp" }), busy);
    setStatus("setting wallpaper…");
    const b = {
      ...Object.fromEntries(params()),
      screens: chosen.join(","),
      fill: fill.value,
    };
    const r = await setWallpaper(state.planner, b);
    if (!r.ok) {
      warn.textContent = "Failed: " + (r.error || "");
      foot.replaceChildren(el("span", { className: "sp" }), cancel, apply);
      return;
    }
    close();
    const parts = [];
    if (r.applied.length) parts.push(`set ✓ on ${r.applied.join(", ")}`);
    if (r.pending && r.pending.length)
      parts.push(`written for ${r.pending.join(", ")} (applies on reconnect)`);
    setStatus(
      parts.length
        ? "wallpaper " + parts.join("; ")
        : `nothing applied - no Plasma desktop matched (detected: ${r.desktops.join(" ")})`,
    );
  };
  modal.append(
    el("h3", {}, "Set as wallpaper"),
    el(
      "label",
      { style: "font-size:12px;color:var(--mut)" },
      "Screens (rendered at current resolution)",
    ),
    list,
    el(
      "div",
      { className: "grp", style: "margin-top:10px" },
      "<label>Fit</label>",
    ),
    warn,
  );
  $(".grp", modal).append(fill);
  const foot = el("div", { className: "foot" });
  foot.append(el("span", { className: "sp" }), cancel, apply);
  modal.append(foot);
  bg.append(modal);
  document.body.append(bg);
}
