# Security Policy

## Reporting a vulnerability

Please report security issues privately via GitHub's
[private vulnerability reporting](https://github.com/dannyadair/timeglance/security/advisories/new)
rather than opening a public issue.

## Scope

timeglance renders local YAML/ICS config to SVG/PDF/PNG and, on KDE Plasma, sets the desktop
wallpaper via `kscreen-doctor`/`dbus-send`. It fetches the `.ics` URLs you configure and starts a
control-panel server bound to localhost (`0.0.0.0` only inside the container you run). It exposes no
other network service.
