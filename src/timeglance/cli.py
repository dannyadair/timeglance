"""The ``timeglance`` command: one entry point with subcommands.

``serve`` runs the on-demand web control panel; ``render year|weekly`` renders a planner to
disk, forwarding the planner's own flags; ``init`` scaffolds the config files from the
bundled templates. Process lifecycle (reboots, backgrounding) is left to systemd or the tray,
so ``serve`` runs in the foreground.
"""

import argparse

from timeglance import init, service
from timeglance.common import schedule, serve
from timeglance.common.log import LOG
from timeglance.planners import PLANNERS
from timeglance.weekly import build as wbuild
from timeglance.year import build as ybuild

RENDERERS = {"year": ybuild.main, "weekly": wbuild.main}


def main(argv=None):
    """Parse the subcommand and dispatch to the control panel, a renderer or the scaffolder."""
    ap = argparse.ArgumentParser(prog="timeglance", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="scaffold year/ and weekly/ config.yaml from the templates")

    sp_serve = sub.add_parser("serve", help="run the web control panel")
    sp_serve.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 in a container)")
    sp_serve.add_argument("--port", type=int, default=8753)

    sp_render = sub.add_parser("render", help="render a planner to disk (see `render <planner> -h` for flags)")
    sp_render.add_argument("planner", choices=RENDERERS)
    sp_render.add_argument("flags", nargs=argparse.REMAINDER, help="flags forwarded to the planner renderer")

    sp_install = sub.add_parser("install", help="install a systemd user timer for the nightly render")
    sp_install.add_argument("--time", help="HH:MM to render at (default: schedule.yaml's time)")
    sub.add_parser("uninstall", help="remove the systemd user timer")
    sub.add_parser("run", help="run the scheduled render once (used by the timer)")

    args = ap.parse_args(argv)
    if args.command == "init":
        init.main()
    elif args.command == "serve":
        serve.run(args.host, args.port)
    elif args.command == "render":
        RENDERERS[args.planner](args.flags)
    elif args.command == "install":
        service.install(args.time)
    elif args.command == "uninstall":
        service.uninstall()
    else:
        schedule.Schedule.load().run_once(PLANNERS, LOG)


if __name__ == "__main__":
    main()
