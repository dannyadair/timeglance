"""System tray controller for the on-demand control panel (KDE/Plasma, via pystray).

A convenience launcher and quick schedule toggles - not the scheduler itself. The nightly
render is driven by the systemd timer from ``timeglance install``, so quitting the tray never
stops a scheduled render; it only closes the panel it started.

Needs the ``[tray]`` extra (``pystray``) plus the system AppIndicator/GObject libraries on KDE
(e.g. ``apt install python3-gi gir1.2-ayatanaappindicator3-0.1``); see the README.
"""

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import pystray
from PIL import Image

from timeglance import service
from timeglance.common import schedule, settings
from timeglance.planners import PLANNERS

ICON = Path(__file__).parent / "common" / "web" / "icon.png"
PORTS = [8753, 8080, 8888]
TIMES = ["05:00", "06:00", "07:00", "08:00", "21:00"]


class Tray:
    """Holds the panel subprocess we own and translates menu clicks into schedule/service edits."""

    def __init__(self):
        self.proc = None

    def running(self):
        """True if something is listening on the configured port."""
        with socket.socket() as s:
            s.settimeout(0.2)
            return s.connect_ex(("127.0.0.1", settings.get_port())) == 0

    def start_server(self):
        if not self.running():
            self.proc = subprocess.Popen([sys.executable, "-m", "timeglance.cli", "serve"])

    def stop_server(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        self.proc = None

    def open_panel(self):
        self.start_server()
        for _ in range(50):
            if self.running():
                break
            time.sleep(0.1)
        webbrowser.open(f"http://127.0.0.1:{settings.get_port()}")

    def set_port(self, port):
        settings.set_port(port)
        if self.proc and self.proc.poll() is None:
            self.stop_server()
            self.start_server()

    def set_time(self, hhmm):
        s = schedule.Schedule.load()
        s.cfg["time"] = hhmm
        s.save()
        if service.enabled():
            service.install()

    def toggle_planner(self, name):
        s = schedule.Schedule.load()
        planners = list(s.cfg.get("planners", []))
        planners.remove(name) if name in planners else planners.append(name)
        s.cfg["planners"] = planners
        s.save()

    def toggle_wallpaper(self, name):
        s = schedule.Schedule.load()
        block = s.planner_block(name)
        block["wallpaper"] = not block["wallpaper"]
        s.cfg[name] = block
        s.save()

    def quit(self, icon):
        self.stop_server()
        icon.stop()

    def menu(self):
        return pystray.Menu(
            pystray.MenuItem("Open control panel", lambda icon, item: self.open_panel(), default=True),
            pystray.MenuItem(
                lambda item: f"● running on :{settings.get_port()}" if self.running() else "○ stopped",
                None,
                enabled=False,
            ),
            pystray.MenuItem(
                lambda item: "Stop server" if self.running() else "Start server",
                lambda icon, item: self.stop_server() if self.running() else self.start_server(),
            ),
            pystray.MenuItem(
                lambda item: f"Port: {settings.get_port()}",
                pystray.Menu(
                    *(
                        pystray.MenuItem(str(p), self._pick_port(p), checked=self._port_is(p), radio=True)
                        for p in PORTS
                    ),
                    pystray.MenuItem("Other… (control panel)", lambda icon, item: self.open_panel()),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Schedule", None, enabled=False),
            pystray.MenuItem(
                "Enabled",
                lambda icon, item: self._toggle_timer(icon),
                checked=lambda item: service.enabled(),
            ),
            pystray.MenuItem(
                lambda item: f"Time: {schedule.Schedule.load().cfg['time']}",
                pystray.Menu(
                    *(pystray.MenuItem(t, self._pick_time(t), checked=self._time_is(t), radio=True) for t in TIMES),
                    pystray.MenuItem("Other… (control panel)", lambda icon, item: self.open_panel()),
                ),
            ),
            pystray.MenuItem(
                "Planners",
                pystray.Menu(
                    *(
                        pystray.MenuItem(name.capitalize(), self._toggle_planner(name), checked=self._planner_on(name))
                        for name in PLANNERS
                    ),
                ),
            ),
            pystray.MenuItem(
                "Wallpaper",
                pystray.Menu(
                    *(
                        pystray.MenuItem(
                            name.capitalize(), self._toggle_wallpaper(name), checked=self._wallpaper_on(name)
                        )
                        for name in PLANNERS
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda icon, item: self.quit(icon)),
        )

    def _pick_port(self, port):
        def action(icon, item):
            self.set_port(port)
            icon.update_menu()

        return action

    def _port_is(self, port):
        return lambda item: settings.get_port() == port

    def _pick_time(self, hhmm):
        def action(icon, item):
            self.set_time(hhmm)
            icon.update_menu()

        return action

    def _time_is(self, hhmm):
        return lambda item: schedule.Schedule.load().cfg["time"] == hhmm

    def _toggle_timer(self, icon):
        service.disable() if service.enabled() else service.enable()
        icon.update_menu()

    def _toggle_planner(self, name):
        def action(icon, item):
            self.toggle_planner(name)
            icon.update_menu()

        return action

    def _planner_on(self, name):
        return lambda item: name in schedule.Schedule.load().cfg.get("planners", [])

    def _toggle_wallpaper(self, name):
        def action(icon, item):
            self.toggle_wallpaper(name)
            icon.update_menu()

        return action

    def _wallpaper_on(self, name):
        return lambda item: schedule.Schedule.load().planner_block(name)["wallpaper"]


def main():
    tray = Tray()
    pystray.Icon("timeglance", Image.open(ICON), "timeglance", menu=tray.menu()).run()


if __name__ == "__main__":
    main()
