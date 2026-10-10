# Configuration

Working configs (`year/config.yaml`, `weekly/config.yaml`) are git-ignored (personal schedule / calendar
secrets); the packaged `config.yaml.in` files are annotated templates. Run `timeglance-init` to scaffold the
working configs from them. Precedence is **built-in defaults < YAML < CLI flags**, so you can comment defaults out
rather than delete them.

See the [Reference](reference.md) for the full list of flags and YAML keys.

## Year (`year/config.yaml`)

- **`range`** - `start`/`end` accept `today`, `today±N` (months), `year-start`, `year-end`, or `YYYY-MM`.
  A shorter range renders larger. Or set a `span` preset instead of `start`/`end`: `this_year`,
  `upcoming_year` (rolling 12 from this month), or `custom` with `before`/`after` month counts.
- **`holidays`** - auto-populated via the [`holidays`](https://pypi.org/project/holidays/) package
  (`country` + `subdiv`, e.g. `NZ` / `WGN`).
- **`sources`** - external iCalendar feeds (see below).
- **`layers`** / **`events`** - a single day uses `date:`, a span uses `start:`+`end:` (inclusive); recurrence via
  `repeat: yearly|weekly|monthly` or a full `rrule:` (RFC 5545 / dateutil).

### Calendar sources (.ics)

Let your existing calendars _be_ the editor. Any number of `.ics` feeds are merged into the event stream and mapped
to a layer:

```yaml
sources:
  - url: "https://calendar.proton.me/api/calendar/v1/url/…/calendar.ics" # a Proton share link
    layer: birthdays
  - path: "~/calendars/my-year.ics" # a local file
    label: My Year # creates a layer if `layer:` is omitted
    color: "#7A7F87"
```

Recurrences, `EXDATE`s and all-day/timed spans are expanded within the render window. URL feeds are TTL-cached
(`refresh:` seconds) under `state/ics-cache`, and a failed refresh falls back to the last good copy. Nice trick:
keep a private "year" calendar you never show online and only export here.

> **A share link is a secret.** Proton links embed a passphrase key. Keep them in your git-ignored `config.yaml`,
> never in the tracked `config.yaml.in`.

## Weekly (`weekly/config.yaml`)

`topics` (label + colour; `visible: false` hides one by default) and a flat list of `activities`. Toggle any
topic in the UI (or with `--hide`/`--only`); comment out a single activity to drop a one-off. `wallpaper:` tunes
the canvas `background`, `margin`, `shadow`, and `screens`.
