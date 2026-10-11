"""Resolve a theme/layout selection, shared by the planners (CLI > YAML > all/fallback)."""


def resolve_list(cli, yaml_val, allowed):
    """Resolve a multi-variant selection (CLI > YAML > all) and validate it against ``allowed``."""
    spec = cli if cli is not None else yaml_val
    if not spec:
        return allowed
    items = [s.strip() for s in str(spec).split(",")]
    bad = [i for i in items if i not in allowed]
    if bad:
        raise SystemExit(f"unknown value(s): {', '.join(bad)} (allowed: {', '.join(allowed)})")
    return items


def pick(cli, yaml_val, fallback, allowed, what):
    """Choose the single variant for the wallpaper: explicit single CLI value > YAML > fallback."""
    val = None
    if cli:
        items = [s.strip() for s in cli.split(",")]
        if len(items) == 1:
            val = items[0]
    val = val or yaml_val or fallback
    if val not in allowed:
        raise SystemExit(f"unknown wallpaper {what}: {val}  (allowed: {', '.join(allowed)})")
    return val
