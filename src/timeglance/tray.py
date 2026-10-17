"""System tray controller for the on-demand control panel (KDE/Plasma, via PySide6/Qt).

A convenience launcher and status readout - not the scheduler itself. The scheduled render is
driven by the schedule's dead switch plus whatever runs it (the systemd timer from
``timeglance install``, or this panel's own loop while it's open), so quitting the tray never
stops a scheduled render; it only closes the panel it started.

Needs the ``[tray]`` extra (``PySide6``); on a Qt desktop like Plasma that's all it takes.
"""

import os
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
from PySide6.QtCore import QTime, QTimer
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QLabel,
    QMenu,
    QSystemTrayIcon,
    QTimeEdit,
    QVBoxLayout,
)

from timeglance import __version__, autostart, init, paths, service
from timeglance.common import schedule, settings, wallpaper
from timeglance.common.log import LOG
from timeglance.planners import PLANNERS

ICON = Path(__file__).parent / "common" / "web" / "icon.png"
DOT_COLORS = {"green": (46, 160, 67), "red": (220, 66, 66), "amber": (224, 160, 48)}


def _qicon(img):
    """A QIcon from a PIL RGBA image."""
    qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format.Format_RGBA8888)
    return QIcon(QPixmap.fromImage(qimg))


def _icon(grey):
    """A QIcon from the bundled PNG; greyed (desaturated, half-alpha) for the server-stopped state."""
    img = Image.open(ICON).convert("RGBA")
    if grey:
        g = ImageOps.grayscale(img)
        alpha = img.getchannel("A").point(lambda a: a // 2)
        img = Image.merge("RGBA", (g, g, g, alpha))
    return _qicon(img)


def _dot(rgb):
    """A small filled-circle QIcon in the given colour, for the server/schedule status indicators."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((3, 3, 12, 12), fill=rgb + (255,))
    return _qicon(img)


class Menu(QMenu):
    """A QMenu that stays open when a checkable item is toggled, so several can be flipped at once."""

    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action is not None and action.isEnabled() and action.isCheckable():
            action.trigger()
            return
        super().mouseReleaseEvent(event)


class Tray:
    """Owns the Qt tray icon and the panel subprocess it starts, and edits the schedule/port."""

    def __init__(self, app):
        self.app = app
        self.proc = None
        self._icon_on = _icon(False)
        self._icon_off = _icon(True)
        self._dots = {name: _dot(rgb) for name, rgb in DOT_COLORS.items()}
        self.menu = Menu()
        self.menu.aboutToShow.connect(self.populate)
        self.tray = QSystemTrayIcon(self._icon_on)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._activated)
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(2000)
        self._tick()
        self.tray.show()

    def running(self):
        """True if something is listening on the configured port."""
        with socket.socket() as s:
            s.settimeout(0.2)
            return s.connect_ex(("127.0.0.1", settings.get_port())) == 0

    def _owned(self):
        """True while the panel process we started is still alive (vs one started elsewhere)."""
        return self.proc is not None and self.proc.poll() is None

    def start_server(self):
        """Start the panel and wait briefly for it to bind; True if it's up, False if it couldn't."""
        if self.running():
            return True
        self.proc = subprocess.Popen([sys.executable, "-m", "timeglance.cli", "serve"])
        for _ in range(50):
            if self.running():
                return True
            if self.proc.poll() is not None:
                return False
            time.sleep(0.1)
        return self.running()

    def stop_server(self):
        """Stop the panel process we started (a server started elsewhere isn't ours to kill)."""
        if self._owned():
            self.proc.terminate()
        self.proc = None

    def open_panel(self):
        """Open the control panel in the browser (the server must already be up)."""
        webbrowser.open(f"http://127.0.0.1:{settings.get_port()}")

    def set_port(self, port):
        """Persist the panel port, restarting our server on the new one if we're running it."""
        settings.set_port(port)
        if self._owned():
            self.stop_server()
            self.start_server()
        self._tick()

    def set_time(self, hhmm):
        """Persist the schedule time, re-writing the systemd timer if it's installed."""
        s = schedule.Schedule.load()
        s.cfg["time"] = hhmm
        s.save()
        if service.enabled():
            service.install()

    def toggle_enabled(self):
        """Flip the schedule's dead switch (persisted; the running scheduler re-reads it on disk)."""
        s = schedule.Schedule.load()
        s.cfg["enabled"] = not s.enabled
        s.save()

    def toggle_autostart(self):
        """Flip the login-autostart entry for the tray."""
        autostart.disable() if autostart.enabled() else autostart.enable()

    def run_now(self):
        """Render the scheduled set now - manual, so it ignores the dead switch."""
        threading.Thread(target=lambda: schedule.Schedule.load().run_once(PLANNERS, LOG), daemon=True).start()
        self.tray.showMessage(
            "timeglance", "Running the scheduled render now…", QSystemTrayIcon.MessageIcon.Information
        )

    # ---- menu assembly --------------------------------------------------------------------

    def _schedule_state(self, s, server, svc):
        """(title, mechanism, dot) describing whether the schedule will fire, honestly at a glance."""
        if not s.enabled:
            return "Schedule disabled", "Disabled — enable to resume", "red"
        if svc:
            return "Scheduled", "Running in the background", "green"
        if server:
            return "Scheduled", "Running while the panel is open", "green"
        return "Schedule paused", "Enabled, but nothing is running it — open the panel or install the service", "amber"

    def _creates(self, s):
        """(files, wallpapers): what a scheduled run writes. files are (label, filename, dims, folder);
        wallpapers are (planner label, screen name, resolution) - what gets set on which screen. Screen
        names and resolutions come from the live/remembered registry so a disconnected one still reads nicely."""
        selected = s.cfg.get("planners", [])
        planners = [n for n in PLANNERS if n in selected]
        label, connected = {}, []
        if any(s.planner_block(n)["wallpaper"] for n in planners):
            known = wallpaper.known(wallpaper.detect())
            label = {k["name"]: (k["model"] or k["name"], f"{k['w']}×{k['h']}") for k in known}
            connected = [k["name"] for k in known if k["connected"]]
        files, wallpapers = [], []
        for name in planners:
            planner = PLANNERS[name]
            block = s.planner_block(name)
            files.append((name.capitalize(), planner.out_name, planner.size_label(block["render"]), str(planner.out)))
            if block["wallpaper"]:
                for scr in block["screens"] or connected:
                    if scr:
                        model, res = label.get(scr, (wallpaper._friendly_name(scr) or scr, ""))
                        wallpapers.append((name.capitalize(), model, res))
        return files, wallpapers

    def populate(self):
        """Rebuild the context menu from live state (called each time it's about to show)."""
        m = self.menu
        m.clear()
        server = self.running()
        svc = service.enabled()
        s = schedule.Schedule.load()
        port = settings.get_port()

        m.addAction("Open timeglance", self._left_click)
        m.addSeparator()

        srv = Menu("Server running" if server else "Server not running", m)
        srv.menuAction().setIcon(self._dots["green" if server else "red"])
        if server:
            srv.addAction("Stop server", self.stop_server).setEnabled(self._owned())
        else:
            srv.addAction("Start server", self._start_clicked)
        srv.addAction(f"Port {port}").setEnabled(False)
        srv.addAction("Change port…", self._change_port)
        m.addMenu(srv)

        title, mech, dot = self._schedule_state(s, server, svc)
        sch = Menu(title, m)
        sch.menuAction().setIcon(self._dots[dot])
        sch.addAction(mech).setEnabled(False)
        sch.addSeparator()
        files, wallpapers = self._creates(s)
        sch.addAction("Files").setEnabled(False)
        if files:
            for name, fname, dims, folder in files:
                text = f"    {name} → {fname}" + (f" ({dims})" if dims else "")
                sch.addAction(text, lambda *a, d=folder: self._open_folder(d))
        else:
            sch.addAction("    (nothing selected)").setEnabled(False)
        if wallpapers:
            sch.addAction("Wallpaper").setEnabled(False)
            for name, model, res in wallpapers:
                sch.addAction(f"    {name} → {model}" + (f" ({res})" if res else "")).setEnabled(False)
        sch.addSeparator()
        en = sch.addAction("Enabled", self.toggle_enabled)
        en.setCheckable(True)
        en.setChecked(s.enabled)
        sch.addAction(f"Daily at {s.cfg['time']}").setEnabled(False)
        sch.addAction("Change time…", self._change_time)
        sch.addAction("Run now", self.run_now)
        m.addMenu(sch)

        m.addSeparator()
        m.addAction(f"timeglance {__version__}").setEnabled(False)
        auto = m.addAction("Autostart tray", self.toggle_autostart)
        auto.setCheckable(True)
        auto.setChecked(autostart.enabled())
        m.addAction("Quit", self.quit).setIcon(QIcon.fromTheme("application-exit"))

    # ---- actions --------------------------------------------------------------------------

    def _activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._left_click()

    def _left_click(self):
        """Left-click / Open: start the server if needed, then open the panel; else say why not."""
        if self.running() or self.start_server():
            self.open_panel()
        else:
            self.tray.showMessage(
                "timeglance",
                f"Couldn't start the server — port {settings.get_port()} may be in use.",
                QSystemTrayIcon.MessageIcon.Warning,
            )
        self._tick()

    def _start_clicked(self):
        if not self.start_server():
            self.tray.showMessage(
                "timeglance",
                f"Couldn't start the server — port {settings.get_port()} may be in use.",
                QSystemTrayIcon.MessageIcon.Warning,
            )
        self._tick()

    def _open_folder(self, path):
        """Open a planner's output folder in the file manager."""
        subprocess.Popen(["xdg-open", path])

    def _change_port(self):
        port, ok = QInputDialog.getInt(None, "timeglance", "Control panel port:", settings.get_port(), 1, 65535)
        if ok:
            self.set_port(port)

    def _change_time(self):
        hh, mm = (int(x) for x in schedule.Schedule.load().cfg["time"].split(":"))
        dlg = QDialog()
        dlg.setWindowTitle("timeglance")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Render daily at:"))
        edit = QTimeEdit(QTime(hh, mm))
        edit.setDisplayFormat("HH:mm")
        layout.addWidget(edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec():
            self.set_time(edit.time().toString("HH:mm"))

    def _tick(self):
        """Poll: reflect the running state in the icon and tooltip."""
        running = self.running()
        self.tray.setIcon(self._icon_on if running else self._icon_off)
        self.tray.setToolTip(f"timeglance — running on :{settings.get_port()}" if running else "timeglance — stopped")

    def quit(self):
        self.stop_server()
        self.app.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        raise SystemExit("no system tray available on this desktop")
    init.ensure()
    tray = Tray(app)
    pid = paths.tray_pid()
    pid.parent.mkdir(parents=True, exist_ok=True)
    pid.write_text(str(os.getpid()))
    signal.signal(signal.SIGTERM, lambda *a: tray.quit())
    try:
        sys.exit(app.exec())
    finally:
        pid.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
