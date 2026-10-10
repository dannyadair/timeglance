// The Schedule overlay: per-planner nightly render, wallpaper targets and render overrides.

import { $, el } from "./dom.js";
import { body, setStatus } from "./state.js";
import { forgetScreen, getSchedule, saveSchedule } from "./api.js";

export async function showSchedule() {
  const s = await getSchedule();
  body.innerHTML = "";
  const wrap = el("div", { className: "sched" });
  wrap.append(
    el(
      "div",
      { className: "sched-head" },
      "<h1>Schedule</h1><p>Daily re-rendering of planners - write their files to disk, set them as desktop wallpaper.</p>",
    ),
  );

  const card = el("div", { className: "card" });
  card.append(
    el(
      "div",
      { className: "grp", style: "margin-bottom:10px" },
      `<span class="dot ${s.running ? "on" : ""}"></span><strong>${s.running ? "Running" : "Stopped"}</strong>`,
    ),
    el(
      "div",
      { className: "grp" },
      `<label>Daily at</label><input id="s_time" value="${s.time}" style="width:70px"><span class="hint">${s.tz}</span>`,
    ),
  );

  // Screen names a planner's config targets that we've never seen (bad id, or state cleared):
  // list them as FYI - we can't know their resolution, so they can't be rendered.
  const unseenOf = (chosen) =>
    chosen
      .filter((n) => !s.screens.some((sc) => sc.name === n))
      .map((n) => ({ name: n, model: "", connected: false, seen: false }));
  const forget = async (name) => {
    await forgetScreen(name);
    showSchedule();
  };
  // One section per planner: render nightly -> write its file; optionally set that file as the
  // wallpaper on chosen screens. A disconnected screen can still be targeted (its file is written
  // now and applied on reconnect), shown as offline with a Forget button to drop a retired monitor.
  const section = (name, label) => {
    const cfg = s.config[name];
    const sec = el("div", { className: "schd-sec" });
    sec.append(
      el(
        "div",
        { className: "grp" },
        `<span data-toggle="s_${name}"><input type="checkbox" class="s-pl" id="s_${name}" value="${name}" ${s.planners.includes(name) ? "checked" : ""}><label><strong>${label}</strong></label></span>
       <code class="dst">→ ${s.outputs[name]}</code>`,
      ),
    );
    sec.append(
      el(
        "div",
        { className: "grp", style: "padding-left:16px" },
        `<span data-toggle="s_wp_${name}"><input type="checkbox" class="s-wp" id="s_wp_${name}" value="${name}" ${cfg.wallpaper ? "checked" : ""}><label>set as wallpaper</label></span>`,
      ),
    );
    const chosen = cfg.screens; // [] means all connected
    const rows = [...s.screens, ...unseenOf(chosen)];
    if (rows.length) {
      const row = el("div", {
        className: "grp schd-scr-row",
        style: "padding-left:32px",
      });
      for (const sc of rows) {
        const seen = sc.seen !== false;
        const on = !seen
          ? true
          : sc.connected
            ? chosen.length === 0 || chosen.includes(sc.name)
            : chosen.includes(sc.name);
        const note = !seen
          ? ' <span class="off">· in config, never seen</span>'
          : sc.connected
            ? ""
            : ` <span class="off">· offline, seen ${sc.last_seen}</span>`;
        const opt = el("span", { className: "schd-scr-opt" });
        const toggle = el(
          "span",
          {},
          `<input type="checkbox" class="schd-scr" data-planner="${name}" value="${sc.name}" ${on ? "checked" : ""}><label>${sc.model || sc.name}${note}</label>`,
        );
        toggle.dataset.toggle = `scr_${name}_${sc.name}`;
        toggle.querySelector("input").id = `scr_${name}_${sc.name}`;
        opt.append(toggle);
        if (!sc.connected && seen) {
          // Remembered-but-offline: Forget drops it from the registry. An unseen screen isn't
          // in the registry; it's removed just by unticking it (dropped from the config on save).
          const f = el(
            "button",
            { className: "forget", title: `Forget ${sc.name}` },
            "Forget",
          );
          f.onclick = () => forget(sc.name);
          opt.append(f);
        }
        row.append(opt);
      }
      sec.append(row);
    }
    // Optional per-planner overrides for the nightly render: top-level YAML, same shape as the
    // planner's config.yaml, so you can paste keys straight across. Folded into schedule.yaml's
    // `render:` block on save. Open by default when something's set so it isn't hidden.
    const det = el("details", {
      className: "schd-ovr",
      style: "padding-left:16px",
    });
    det.open = !!cfg.render_yaml;
    det.append(el("summary", {}, "Render overrides (YAML)"));
    const ta = el("textarea", {
      id: `s_render_${name}`,
      className: "ovr-yaml",
      spellcheck: false,
    });
    ta.value = cfg.render_yaml || "";
    ta.placeholder =
      name === "year" ? "theme: dark\nlayout: compact" : "paper: A3";
    det.append(ta);
    sec.append(det);
    // Setting a wallpaper only makes sense if the file gets rendered, so the wallpaper toggle,
    // screen targets and overrides dim out (and stop responding) until the planner is ticked to run.
    const render = sec.querySelector(`#s_${name}`);
    const dim = sec.querySelectorAll(`#s_wp_${name}, .schd-scr-row, .schd-ovr`);
    const sync = () => {
      sec
        .querySelectorAll(
          `#s_wp_${name}, input.schd-scr[data-planner="${name}"], #s_render_${name}`,
        )
        .forEach((i) => (i.disabled = !render.checked));
      dim.forEach((d) =>
        (d.closest(".grp") || d).classList.toggle("off-dim", !render.checked),
      );
    };
    render.addEventListener("change", sync);
    sync();
    return sec;
  };
  card.append(section("year", "Year"), section("weekly", "Weekly"));

  const bar = el("div", { className: "grp", style: "margin-top:14px" });
  const start = el("button", { className: "primary" }, "Start");
  const stop = el("button", {}, "Stop");
  const runNow = el("button", {}, "Run now");
  bar.append(
    start,
    stop,
    runNow,
    el(
      "span",
      { style: "font-size:12px;color:var(--mut)" },
      `${s.last_run ? "last " + s.last_run : ""}${s.next_run ? "  ·  next " + s.next_run : ""}`,
    ),
  );
  card.append(bar);

  const connectedNames = s.screens
    .filter((sc) => sc.connected)
    .map((sc) => sc.name);
  const collect = (action) => {
    const cfg = {
      time: $("#s_time").value,
      planners: [...card.querySelectorAll("input.s-pl:checked")].map(
        (c) => c.value,
      ),
      action,
    };
    for (const name of ["year", "weekly"]) {
      const block = { wallpaper: $(`#s_wp_${name}`).checked };
      const boxes = [
        ...card.querySelectorAll(`input.schd-scr[data-planner="${name}"]`),
      ];
      if (boxes.length) {
        const chosen = boxes.filter((c) => c.checked).map((c) => c.value);
        // All connected ticked (and nothing else) == "all" ([]), so a new screen is still covered.
        const allConnected =
          chosen.length === connectedNames.length &&
          connectedNames.every((n) => chosen.includes(n));
        block.screens = allConnected ? [] : chosen;
      }
      block.render = $(`#s_render_${name}`).value;
      cfg[name] = block;
    }
    return cfg;
  };
  const post = async (action) => {
    const r = await saveSchedule(collect(action));
    if (!r.ok) {
      // Keep the panel (and the user's typed YAML) as-is; just report what's wrong.
      setStatus(
        (await r.json().catch(() => ({}))).error ||
          `schedule not saved (${r.status})`,
      );
      return;
    }
    showSchedule();
  };
  start.onclick = () => post("start");
  stop.onclick = () => post("stop");
  runNow.onclick = () => post("run");

  wrap.append(card);
  body.append(wrap);
}
