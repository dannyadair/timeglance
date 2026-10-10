# The control panel

Open <http://localhost:8753>. Switch **Weekly / Year**, and within each, switch the view:

- **Preview** - live render with quick controls (year: theme, layout, week start, range, size, layer toggles;
  weekly: paper, activity toggles). **Export** (PNG / PDF) and **Set as wallpaper** act on the current controls.
- **Config** - the planner's full YAML in an editor. **Save** validates and writes it; **Reset to template** restores
  the annotated template. This is the source of truth - anything not in the quick controls lives here.

Two shared, app-wide views sit alongside them:

- **Schedule** - a daily loop that re-renders the ticked planners and writes each one's file to disk
  (`year/out/year.png`, `weekly/out/weekly.pdf`); **set as wallpaper** is an optional extra on top. Pick a time
  (shown with the machine's timezone), then **Start / Stop / Run now**. With more than one screen you can assign
  each planner to specific outputs (e.g. weekly on the laptop, year on the ultrawide); leave all ticked to target
  every screen. Runs are isolated so one failing planner can't sink the rest. Config lives in `schedule.yaml` at
  the project root; add a per-planner `render:` block there to override the scheduled render (same keys as the
  quick controls), e.g. a darker theme or a specific size.
- **Log** - a persistent activity log of every render, export and wallpaper change, scheduled or manual (live
  previews aren't logged). **Clear log** wipes it (with confirmation). The activity log persists under `state/`;
  the schedule lives in `schedule.yaml`.

The YAML is re-read on every request, so external edits show up on reload.
