// Thin wrappers over the /api/* endpoints. GET helpers return parsed JSON; the schedule and
// forget writes return the raw Response/promise so callers can inspect HTTP status themselves.

import { state } from "./state.js";

export async function loadConfig(planner) {
  state.cfg[planner] = await fetch("/api/config?planner=" + planner).then((r) =>
    r.json(),
  );
}

export const getSchedule = () => fetch("/api/schedule").then((r) => r.json());

export const getLog = () => fetch("/api/log").then((r) => r.json());

export const saveConfig = (planner, yaml) =>
  fetch("/api/config?planner=" + planner, {
    method: "POST",
    body: JSON.stringify({ yaml }),
  }).then((r) => r.json());

export const resetConfig = (planner) =>
  fetch("/api/config/reset?planner=" + planner, { method: "POST" }).then((r) =>
    r.json(),
  );

export const clearLog = () => fetch("/api/log/clear", { method: "POST" });

export const forgetScreen = (name) =>
  fetch("/api/screens/forget", {
    method: "POST",
    body: JSON.stringify({ name }),
  });

export const saveSchedule = (cfg) =>
  fetch("/api/schedule", { method: "POST", body: JSON.stringify(cfg) });

export const setWallpaper = (planner, body) =>
  fetch("/api/wallpaper?planner=" + planner, {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => r.json());
