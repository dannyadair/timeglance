// Shared UI state, the long-lived layout element refs, and the status line.

import { $ } from "./dom.js";

export const state = {
  planner: "weekly",
  view: "preview",
  prevView: "preview",
  cfg: {},
};

export const side = $("#side");
export const body = $("#viewbody");
export const controls = $("#controls");
export const actions = $("#actions");
export const status = $("#status");

export const LOADING_PANE =
  '<div class="preview-pane loading"><div class="load-ov"><div class="spinner"></div></div></div>';

export function setStatus(msg) {
  status.textContent = msg || "";
}
