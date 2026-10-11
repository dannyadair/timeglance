#!/usr/bin/env bash
# Build a timeglance .deb: a self-contained venv under /opt/timeglance built against the
# distro's system python3 (3.12 on Ubuntu 24.04), fronted by a /usr/bin/timeglance launcher.
# Run inside the target distro (e.g. ubuntu:24.04) so the venv's interpreter matches the one
# the package Depends on. Writes timeglance_<version>_<arch>.deb into the current directory.
set -euo pipefail

VERSION="${1:?usage: build-deb.sh VERSION WHEEL}"
WHEEL="${2:?usage: build-deb.sh VERSION WHEEL}"
ARCH="$(dpkg --print-architecture)"
HERE="$(cd "$(dirname "$0")" && pwd)"
PREFIX=/opt/timeglance
STAGE="$(mktemp -d)"

# Native libraries WeasyPrint/CairoSVG load at runtime (mirrors the Dockerfile), the system
# interpreter the bundled venv points at, the fonts the templates reference, and the tray's
# AppIndicator/GObject stack - the tray ships in the package, so its venv is built with
# --system-site-packages to import the system `gi` that pip can't provide.
DEPENDS="python3 (>= 3.12), python3-gi, gir1.2-ayatanaappindicator3-0.1, libcairo2, libpango-1.0-0, libpangocairo-1.0-0, libgdk-pixbuf-2.0-0, libffi8, shared-mime-info, fonts-dejavu-core, fonts-noto-core"

python3 -m venv --system-site-packages "$PREFIX"
"$PREFIX/bin/pip" install --no-cache-dir "${WHEEL}[tray]"

install -d "$STAGE$PREFIX" "$STAGE/usr/bin" "$STAGE/usr/share/applications" \
          "$STAGE/usr/share/icons/hicolor/scalable/apps" "$STAGE/DEBIAN"
cp -a "$PREFIX/." "$STAGE$PREFIX/"
ln -s "$PREFIX/bin/timeglance" "$STAGE/usr/bin/timeglance"
install -m644 "$HERE/timeglance.desktop" "$STAGE/usr/share/applications/timeglance.desktop"
install -m644 "$(ls "$PREFIX"/lib/python*/site-packages/timeglance/common/web/favicon.svg)" \
        "$STAGE/usr/share/icons/hicolor/scalable/apps/timeglance.svg"

cat > "$STAGE/DEBIAN/control" <<CTL
Package: timeglance
Version: $VERSION
Architecture: $ARCH
Maintainer: Danny W. Adair <danny.adair@unfold.nz>
Depends: $DEPENDS
Section: utils
Priority: optional
Homepage: https://github.com/dannyadair/timeglance
Description: A printable weekly routine sheet and a year-at-a-glance planner.
 A config-driven weekly routine sheet, a year-at-a-glance planner and a web
 control panel, with KDE Plasma desktop-wallpaper rendering.
CTL

dpkg-deb --build --root-owner-group "$STAGE" "timeglance_${VERSION}_${ARCH}.deb"
