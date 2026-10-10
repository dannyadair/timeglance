# Wallpaper (KDE Plasma)

Auto-detected; the button only appears where it's supported. Each chosen screen is rendered at its **current
resolution** and set as that screen's background; the others are left untouched. The weekly sheet, being
page-shaped, is centred on a themed canvas (with a soft drop shadow) and letterboxed on wide screens.

Output goes to each planner's `out/` as a stable `{planner}-wallpaper-{screen}.png`, overwritten in place (one
file per screen; screens sharing a resolution reuse a single render). The stable name is deliberate: a screen
that was disconnected at render time still picks up the fresh image when it reconnects, because Plasma remembers
its path and reloads from disk. Plasma's `org.kde.image` otherwise only reloads when the image config string
changes, so each apply appends a throwaway `#<stamp>` fragment to the `file://` path - that changes the string
(forcing a reload) while Qt strips the fragment and loads the same file. Configure defaults under `wallpaper:`
in each YAML (`screens`, `fill`, `background`/`margin`/`shadow` for weekly, `theme`/`layout` for year).

Wallpaper-setting is **host-only** - see [Limitations](../README.md#limitations).
