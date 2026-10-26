# Wallpaper (KDE Plasma)

Auto-detected; the button only appears where it's supported. Each chosen screen is rendered at **its own
resolution** and set as that screen's background; the others are left untouched. The weekly sheet, being
page-shaped, is centred on a themed canvas (with a soft drop shadow) and letterboxed on wide screens.

The wallpaper is always a dedicated per-screen PNG rendered fresh for the screen - the weekly sheet is
rasterised from its PDF (with poppler's `pdftocairo`, from `poppler-utils`) onto the canvas - so it is never the
`.pdf`/`.png`/`.svg` you export or print. Those export artifacts and the wallpaper images are written side by
side in the planner's `out/`.

Screens read by a friendly name - the monitor's model from its EDID (or "Built-in display" for a laptop panel),
falling back to the manufacturer + connector, then the bare connector name. Identity is the EDID serial: a
dock that re-enumerates the same panel under a new connector is one screen; two panels of the same model stay
two. The extra connector name is kept as an alias so a schedule that still names the old one applies to the
live output.

Resolution is never configured - it comes from the screen: its current mode when connected, or the last-seen
size for a screen that's remembered but disconnected. timeglance remembers every screen it has seen connected
(in `state/screens.json`, pruned after 30 days), so you can target one that's currently unplugged: its file is
still rendered and written at the remembered resolution. Opening the Schedule view (or the next scheduled
run, if the screen is already back) applies that file to the live output, including when it came back on a
new connector. A screen named in config that's never been seen has no resolution, so it can't be rendered -
it's shown as FYI ("in config, never seen") and skipped rather than erroring.

Output goes to each planner's `out/` as a stable `{planner}-wallpaper-{screen}.png`, overwritten in place (one
file per screen; screens sharing a resolution reuse a single render). The stable name is deliberate: a screen
that was disconnected at render time still picks up the fresh image when it reconnects, because Plasma remembers
its path and reloads from disk. Plasma's `org.kde.image` otherwise only reloads when the image config string
changes, so each apply appends a throwaway `#<stamp>` fragment to the `file://` path - that changes the string
(forcing a reload) while Qt strips the fragment and loads the same file. Configure the Set-as-wallpaper dialog (and CLI) defaults under `wallpaper:`
in each planner YAML (`screens`, `fill`; `background` (`auto` follows the theme, or a colour)/`margin`/`shadow` for weekly;
`theme`/`layout` for both). The nightly job has its own target list in `schedule.yaml`.

Setting the wallpaper needs a live Plasma session, so it isn't available inside the
[Docker test drive](../README.md#try-it-instantly-docker).
