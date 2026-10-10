# Wallpaper (KDE Plasma)

Auto-detected; the button only appears where it's supported. Each chosen screen is rendered at **its own
resolution** and set as that screen's background; the others are left untouched. The weekly sheet, being
page-shaped, is centred on a themed canvas (with a soft drop shadow) and letterboxed on wide screens.

Resolution is never configured - it comes from the screen: its current mode when connected, or the last-seen
size for a screen that's remembered but disconnected. timeglance remembers every screen it has seen connected
(in `state/screens.json`, pruned after 30 days), so you can target one that's currently unplugged: its file is
still rendered and written at the remembered resolution, and Plasma picks it up when the screen reconnects. A
screen named in config that's never been seen has no resolution, so it can't be rendered - it's shown as FYI
("in config, never seen") and skipped rather than erroring.

Output goes to each planner's `out/` as a stable `{planner}-wallpaper-{screen}.png`, overwritten in place (one
file per screen; screens sharing a resolution reuse a single render). The stable name is deliberate: a screen
that was disconnected at render time still picks up the fresh image when it reconnects, because Plasma remembers
its path and reloads from disk. Plasma's `org.kde.image` otherwise only reloads when the image config string
changes, so each apply appends a throwaway `#<stamp>` fragment to the `file://` path - that changes the string
(forcing a reload) while Qt strips the fragment and loads the same file. Configure defaults under `wallpaper:`
in each YAML (`screens`, `fill`, `background`/`margin`/`shadow` for weekly, `theme`/`layout` for year).

Wallpaper-setting is **host-only** - see [Limitations](../README.md#limitations).
