#!/usr/bin/env bash
# Build a Debian-native timeglance .deb: the pure-Python package under
# /usr/lib/python3/dist-packages, run by the distro's own python3, with every
# dependency satisfied by the distro's apt packages (Depends:). No bundled
# interpreter, venv or wheels, so apt matches each dependency's C extensions to
# the system python automatically. Writes timeglance_<version>_all.deb into the
# current directory.
set -euo pipefail

VERSION="${1:?usage: build-deb.sh VERSION}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
STAGE="$(mktemp -d)"
chmod 755 "$STAGE"
SITE=/usr/lib/python3/dist-packages

# Every runtime dependency as a distro package: apt resolves the ABI-matching
# build for the system python3. python3-gi + the AppIndicator typelib back the
# tray; poppler-utils rasterises the weekly PDF for the wallpaper; weasyprint and
# python3-cairosvg pull their own native (Cairo/Pango) stack.
DEPENDS="python3, python3-yaml, python3-jinja2, weasyprint, python3-cairosvg, python3-dateutil, python3-icalendar, python3-recurring-ical-events, python3-holidays, python3-pil, python3-pystray, python3-gi, gir1.2-ayatanaappindicator3-0.1, poppler-utils, fonts-dejavu-core, fonts-noto-core"

install -d "$STAGE$SITE" "$STAGE/usr/bin" "$STAGE/usr/share/applications" \
          "$STAGE/usr/share/icons/hicolor/scalable/apps" \
          "$STAGE/usr/share/metainfo" "$STAGE/usr/share/doc/timeglance" "$STAGE/DEBIAN"

# The package verbatim from the source tree (pure Python plus its web/template data).
cp -a "$REPO/src/timeglance" "$STAGE$SITE/timeglance"
find "$STAGE$SITE/timeglance" -name __pycache__ -type d -prune -exec rm -rf {} +

cat > "$STAGE/usr/bin/timeglance" <<'LAUNCH'
#!/usr/bin/python3
from timeglance.cli import main

raise SystemExit(main())
LAUNCH
chmod 755 "$STAGE/usr/bin/timeglance"

install -m644 "$HERE/timeglance.desktop" "$STAGE/usr/share/applications/timeglance.desktop"
install -m644 "$REPO/src/timeglance/common/web/favicon.svg" \
        "$STAGE/usr/share/icons/hicolor/scalable/apps/timeglance.svg"
install -m644 "$HERE/nz.unfold.timeglance.metainfo.xml" \
        "$STAGE/usr/share/metainfo/nz.unfold.timeglance.metainfo.xml"
install -m644 "$HERE/copyright" "$STAGE/usr/share/doc/timeglance/copyright"

cat > "$STAGE/DEBIAN/control" <<CTL
Package: timeglance
Version: $VERSION
Architecture: all
Maintainer: Danny W. Adair <danny.adair@unfold.nz>
Depends: $DEPENDS
Section: utils
Priority: optional
Homepage: https://github.com/dannyadair/timeglance
Description: A printable weekly routine sheet and a year-at-a-glance planner.
 A config-driven weekly routine sheet, a year-at-a-glance planner and a web
 control panel, with KDE Plasma desktop-wallpaper rendering.
CTL

dpkg-deb --build --root-owner-group "$STAGE" "timeglance_${VERSION}_all.deb"
