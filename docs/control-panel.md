# The control panel

Open <http://localhost:8753>. Switch **Weekly / Year**, and within each, switch the view:

- **Preview** - live render with quick controls (year: theme, layout, week start, range, size, layer toggles;
  weekly: theme, layout, paper, topic toggles). **Export** (PNG / PDF) saves to the planner's `out/`; **Set as wallpaper**
  opens a dialog to pick target screens (including remembered-but-offline ones, with **Forget**) and a fit mode,
  then applies to the live desktop. Both act on the current controls.
- **Config** - the planner's full YAML in an editor. **Save** validates and writes it; **Reset to template** restores
  the annotated template. This is the source of truth - anything not in the quick controls lives here.

Two shared, app-wide views sit alongside them:

- **Schedule** - a daily re-render of the ticked planners, writing each one's file to disk
  (`year/out/year.png`, `weekly/out/weekly.pdf`). Pick a time (shown with the machine's timezone), edit the
  per-planner blocks, then **Save**; **Render now** runs it once immediately. What _triggers_ the daily run is
  the environment's call, not a toggle, and the screen says which: a systemd user timer once you click
  **Install as service** (runs even with the panel closed), otherwise this server's own loop (only while it's
  running). Where there's no systemd (e.g. Docker) the install button is absent and it's always the in-server
  loop. Each ticked planner gets its own block: a **set as wallpaper** toggle and its target screens (send
  weekly to the laptop and year to the ultrawide, or leave all ticked for every screen). Those controls grey
  out until the planner itself is ticked to render. Target screens include ones that are remembered but
  currently disconnected (**Forget** drops them); a screen named in config that's never been seen shows as FYI
  only. Runs are isolated so one failing planner can't sink the rest. Config lives in `schedule.yaml` in the
  state directory; the **Render overrides (YAML)** box under each planner writes a `render:` block there to
  override the scheduled render (same keys as the quick controls), e.g. a darker theme or a size.
- **Log** - a persistent activity log of what timeglance does: startup, config changes, renders, exports and
  wallpaper changes, scheduled or manual (live previews aren't logged). Lines are also echoed to the server's
  stdout. **Clear log** wipes it (with confirmation). The activity log persists in the state directory; the
  schedule lives in `schedule.yaml`.

The YAML is re-read on every request, so external edits show up on reload.
