#!/usr/bin/env bash
# Smoke-test an installed timeglance .deb: the import that used to crash, the CLI,
# both renders, and the poppler-backed wallpaper rasterisation. Run in a fresh
# container after `apt-get install ./timeglance_*.deb` (which pulls the Depends).
set -euo pipefail

export TIMEGLANCE_HOME="$(mktemp -d)"

python3 -c "import timeglance.cli"
timeglance --help >/dev/null
timeglance init
timeglance render year
timeglance render weekly

python3 - <<'PY'
import tempfile
from pathlib import Path
from types import SimpleNamespace

from timeglance.weekly import build as wb

cfg = wb.load(wb.TEMPLATE)
pdf = wb.render_pdf(cfg, None, "A4")
render = wb.make_wallpaper_renderer(pdf, "#2b2f36", 0.05, wb.resolve_shadow({}))
out = Path(tempfile.mkdtemp()) / "wp.png"
render(SimpleNamespace(pw=2560, ph=1440), out)
assert out.stat().st_size > 0, "empty wallpaper"
print("wallpaper rasterised:", out.stat().st_size, "bytes")
PY

echo "smoke test OK"
