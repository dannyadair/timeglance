# The control panel

Open <http://localhost:8753>. Switch **Weekly / Year**, and within each, switch the view:

- **Preview** - live render with quick controls (year: theme, layout, week start, range, size, layer toggles;
  weekly: paper, activity toggles). **Export** (PNG / PDF) and **Set as wallpaper** act on the current controls.
- **Config** - the tool's full YAML in an editor. **Save** validates and writes it; **Reset to template** restores
  the annotated template. This is the source of truth - anything not in the quick controls lives here.

Two shared, app-wide views sit alongside them:

- **Schedule** - a daily re-render loop: pick a time and which tools to refresh (optionally setting the wallpaper),
  **Start / Stop / Run now**. With more than one screen you can assign each tool to specific outputs (e.g. weekly on
  the laptop, year on the ultrawide); leave all ticked to target every screen. Runs are isolated so one failing feed
  can't sink the rest.
- **Log** - a persistent activity log of every render, export and wallpaper change, scheduled or manual (live
  previews aren't logged). **Clear log** wipes it (with confirmation). Schedule config and the log persist under
  `state/`.

The YAML is re-read on every request, so external edits show up on reload.
