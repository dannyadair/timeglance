# The control panel

Open <http://localhost:8753>. Switch **Weekly / Year**, and within each, switch the view:

- **Preview** - live render with quick controls (year: theme, layout, week start, range, size, layer toggles;
  weekly: paper, topic toggles). **Export** (PNG / PDF) saves to the planner's `out/`; **Set as wallpaper**
  opens a dialog to pick target screens (including remembered-but-offline ones, with **Forget**) and a fit mode,
  then applies to the live desktop. Both act on the current controls.
- **Config** - the planner's full YAML in an editor. **Save** validates and writes it; **Reset to template** restores
  the annotated template. This is the source of truth - anything not in the quick controls lives here.

Two shared, app-wide views sit alongside them:

- **Schedule** - a daily loop that re-renders the ticked planners and writes each one's file to disk
  (`year/out/year.png`, `weekly/out/weekly.pdf`). Pick a time (shown with the machine's timezone), then
  **Start / Stop / Run now**. Each ticked planner gets its own block: a **set as wallpaper** toggle and its
  target screens (send weekly to the laptop and year to the ultrawide, or leave all ticked for every screen).
  Those controls grey out until the planner itself is ticked to render. Target screens include ones that are
  remembered but currently disconnected (**Forget** drops them); a screen named in config that's never been
  seen shows as FYI only. Runs are isolated so one failing planner can't sink the rest. Config lives in
  `schedule.yaml` at the project root; the **Render overrides (YAML)** box under each planner writes a `render:`
  block there to override the scheduled render (same keys as the quick controls), e.g. a darker theme or a size.
- **Log** - a persistent activity log of every render, export and wallpaper change, scheduled or manual (live
  previews aren't logged). **Clear log** wipes it (with confirmation). The activity log persists under `state/`;
  the schedule lives in `schedule.yaml`.

The YAML is re-read on every request, so external edits show up on reload.
