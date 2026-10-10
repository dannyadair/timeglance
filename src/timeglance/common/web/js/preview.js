// The live preview pane: year renders inline SVG, weekly loads its HTML sheet in an iframe.

import { $, el } from "./dom.js";
import { body, LOADING_PANE, setStatus, state } from "./state.js";
import { params } from "./params.js";

export async function preview() {
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
