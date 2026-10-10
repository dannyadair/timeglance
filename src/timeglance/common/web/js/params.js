// Build the query params for a preview/export/wallpaper request from the current controls.

import { $ } from "./dom.js";
import { side, state } from "./state.js";

export function params() {
  const p = new URLSearchParams({ planner: state.planner });
  const hide = [
    ...side.querySelectorAll("input[data-layer]:not(:checked)"),
  ].map((c) => c.value);
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
