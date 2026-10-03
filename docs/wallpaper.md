# Wallpaper (KDE Plasma)

Auto-detected; the button only appears where it's supported. Each chosen screen is rendered at its **native
resolution** and set as that screen's background; the others are left untouched. The weekly sheet, being
page-shaped, is centred on a themed canvas (with a soft drop shadow) and letterboxed on wide screens.

Output goes to each tool's `out/` as `{tool}-wallpaper-{w}x{h}-{stamp}.png`; screens sharing a resolution reuse one
file, and each run prunes the tool's older files of that resolution. The filename changes every run on purpose -
Plasma's `org.kde.image` only reloads when the image path changes, so a stable name would leave the old pixmap in
place. Configure defaults under `wallpaper:` in each YAML (`screens`, `fill`, `background`/`margin`/`shadow` for
weekly, `theme`/`layout` for year).

Wallpaper-setting is **host-only** - see [Limitations](../README.md#limitations).
